"""
DRF API views for resumes, analysis, and history.

The analysis flow is a two-request affair exactly like the server-rendered app:
``POST /api/resumes/`` creates ``Resume`` + ``ResumeAnalysis``, and
``GET /api/resumes/<pk>/analysis/`` computes or retrieves the results. All
pipeline work is delegated to the existing services (``read_file_bytes``,
``build_cache_key``, ``run_analysis_pipeline``) — no logic is duplicated here.

Every resume lookup is scoped to ``request.user``, so a foreign resume id is a
404 (never a 403 leak) — no IDOR.
"""
import logging

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .ai.service import get_ai_service
from .models import Resume, ResumeAnalysis
from .serializers import (
    ResumeAnalysisSerializer,
    ResumeCreateSerializer,
    ResumeHistorySerializer,
    ResumeSerializer,
)
from .services import (
    build_cache_key,
    read_file_bytes,
    run_analysis_pipeline,
)
from .views import _delete_storage_file

logger = logging.getLogger(__name__)


class ResumeAnalysisError(Exception):
    """Raised when the analysis pipeline cannot complete for a resume.

    Carries a user-facing message and an HTTP status code:
    - 404 when the stored file is gone and there is no cached result.
    - 400 when the pipeline (or file parsing) fails.
    """

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def run_or_retrieve_analysis(resume: Resume) -> ResumeAnalysis:
    """Return the freshest analysis for a resume, computing it if needed.

    Mirrors ``resume.views.analyze_resume``: cache-hit returns the stored
    ``resume_json`` result, cache-miss runs the full pipeline once and persists
    the outcome (including cached AI explanation/rewrite when the service is
    enabled).
    """
    analysis, _ = ResumeAnalysis.objects.get_or_create(resume=resume)

    # ------------------------------------------------------------------
    # Read the PDF bytes once. Unreadable files degrade gracefully: return
    # the last cached analysis if one exists, otherwise fail cleanly.
    # ------------------------------------------------------------------
    pdf_bytes = read_file_bytes(resume.file)

    if pdf_bytes is None:
        if analysis.resume_json:
            return analysis
        raise ResumeAnalysisError(
            "Resume file not found. It may have been removed after a server "
            "restart. Please upload the resume again.",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    job_description = analysis.job_description

    # Cache short-circuit: same file + same JD -> reuse the stored payload.
    cached = analysis.resume_json or {}
    meta = cached.get("_meta") or {}
    cache_key = build_cache_key(pdf_bytes, job_description)

    if meta.get("cache_key") == cache_key:
        logger.info("api analysis: cache HIT resume_id=%s", resume.id)
        return analysis
    logger.info("api analysis: cache MISS resume_id=%s", resume.id)

    # ------------------------------------------------------------------
    # Cache miss: run the full pipeline once and persist the results.
    # ------------------------------------------------------------------
    try:
        _, payload = run_analysis_pipeline(pdf_bytes, job_description)
    except Exception:
        logger.exception("API analysis failed for resume id=%s", resume.id)
        raise ResumeAnalysisError(
            "Could not analyze this PDF. It may be corrupted or scanned "
            "without an extractable text layer."
        )

    ats = payload["ats"]
    job = payload["job"]

    analysis.ats_score = ats["ats_score"]
    analysis.job_match_score = job["job_fit_score"]
    analysis.recommendations = ats["recommendations"]
    analysis.strengths = ats["strengths"]
    analysis.improvement_areas = ats["improvements"]
    analysis.resume_json = payload
    analysis.save()
    logger.info("api analysis: persisted resume_id=%s", resume.id)

    # AI explanation/rewrite are best-effort enrichment layered on top of the
    # already-persisted deterministic results. The service already degrades to
    # None on provider/validation errors; this outer guard makes it impossible
    # for any unexpected AI-side exception to fail a completed analysis.
    try:
        ai_service = get_ai_service()
        if ai_service._enabled:
            ai_explanation = ai_service.explain(ats, job, payload["text"])
            ai_rewrite = ai_service.rewrite(ats, job, payload["text"])

            if ai_explanation:
                analysis.ai_explanation = ai_explanation.model_dump(mode="json")
            if ai_rewrite:
                analysis.ai_rewrite = ai_rewrite.model_dump(mode="json")
            if ai_explanation or ai_rewrite:
                analysis.save(update_fields=["ai_explanation", "ai_rewrite"])
    except Exception:
        logger.exception(
            "AI enrichment failed for resume_id=%s; deterministic analysis preserved",
            resume.id,
        )

    return analysis


def _user_resumes(user) -> QuerySet:
    """Owner-scoped resume queryset with eager analysis access."""
    return (
        Resume.objects.filter(user=user, is_deleted=False)
        .select_related("analysis")
    )


class ResumeListCreateView(ListCreateAPIView):
    """``GET``/``POST /api/resumes/`` — list own resumes or upload a new one."""

    serializer_class = ResumeSerializer

    def get_queryset(self):
        return _user_resumes(self.request.user)

    def get_serializer_class(self):
        return ResumeCreateSerializer if self.request.method == "POST" else ResumeSerializer

    def create(self, request, *args, **kwargs):
        serializer = ResumeCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        resume = serializer.save()
        return Response(
            ResumeSerializer(resume, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ResumeDetailView(RetrieveDestroyAPIView):
    """``GET``/``DELETE /api/resumes/<pk>/`` — own resume only (404 otherwise)."""

    serializer_class = ResumeSerializer

    def get_queryset(self):
        return _user_resumes(self.request.user)

    def perform_destroy(self, instance):
        # Hard-delete mirroring resume.views.delete_resume: storage file
        # cleanup (PDF + job image), analysis row, then the resume row.
        _delete_storage_file(instance.file)
        if hasattr(instance, "analysis"):
            _delete_storage_file(instance.analysis.job_image)
            instance.analysis.delete()
        instance.delete()


class ResumeAnalysisView(APIView):
    """``GET /api/resumes/<pk>/analysis/`` — compute or retrieve results."""

    def get(self, request, pk):
        resume = get_object_or_404(
            Resume,
            id=pk,
            user=request.user,
            is_deleted=False,
        )
        try:
            analysis = run_or_retrieve_analysis(resume)
        except ResumeAnalysisError as exc:
            return Response({"detail": exc.message}, status=exc.status_code)
        return Response(ResumeAnalysisSerializer(analysis).data)


class HistoryView(APIView):
    """``GET /api/history/`` — compact, newest-first list of own resumes."""

    def get(self, request):
        resumes = _user_resumes(request.user).order_by("-uploaded_at")
        return Response(
            ResumeHistorySerializer(resumes, many=True).data,
        )