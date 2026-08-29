import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import ResumeForm
from .models import Resume, ResumeAnalysis
from .services import (
    build_cache_key,
    context_from_payload,
    read_file_bytes,
    run_analysis_pipeline,
)
from .ai.service import get_ai_service

logger = logging.getLogger(__name__)


@login_required
def upload_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)

        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()

            # Always create a fresh analysis for every upload
            ResumeAnalysis.objects.create(
                resume=resume,
                job_description=form.cleaned_data.get(
                    "job_description",
                    "",
                ),
                job_image=form.cleaned_data.get(
                    "job_image",
                ),
            )

            messages.success(
                request,
                "Resume uploaded successfully.",
            )

            return redirect(
                "analyze_resume",
                resume.id,
            )

    else:
        form = ResumeForm()

    return render(
        request,
        "resume/upload.html",
        {
            "form": form,
        },
    )


@login_required
def resume_history(request):
    resumes = (
        Resume.objects.filter(
            user=request.user,
            is_deleted=False,
        )
        .select_related("analysis")
        .order_by("-uploaded_at")
    )

    return render(
        request,
        "resume/history.html",
        {
            "resumes": resumes,
        },
    )


@login_required
def analyze_resume(request, resume_id):
    logger.info("analyze_resume: start resume_id=%s user_id=%s", resume_id, request.user.id)
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user,
        is_deleted=False,
    )
    logger.info("analyze_resume: resume retrieved id=%s file=%s", resume.id, getattr(resume.file, "name", None))

    analysis, created = ResumeAnalysis.objects.get_or_create(
        resume=resume,
    )
    logger.info("analyze_resume: ResumeAnalysis %s id=%s", "created" if created else "retrieved", analysis.id)

    # ------------------------------------------------------------------
    # Read the PDF bytes once. Unreadable files degrade gracefully: render
    # the last cached analysis if one exists, otherwise explain and redirect.
    # ------------------------------------------------------------------
    logger.info("analyze_resume: read_file_bytes start")
    pdf_bytes = read_file_bytes(resume.file)
    logger.info("analyze_resume: read_file_bytes end bytes=%s", len(pdf_bytes) if pdf_bytes else None)

    if pdf_bytes is None:
        logger.warning("analyze_resume: pdf_bytes is None, file unreadable")
        if analysis.resume_json:
            context = context_from_payload(analysis.resume_json)
            # Include cached AI results from the model
            context["ai_explanation"] = analysis.ai_explanation
            context["ai_rewrite"] = analysis.ai_rewrite
            return render(
                request,
                "resume/analysis.html",
                {**context, "resume": resume, "analysis": analysis},
            )

        messages.error(
            request,
            "Resume file not found. It may have been removed after a server "
            "restart. Please upload the resume again.",
        )
        return redirect("upload_resume")

    job_description = analysis.job_description

    # ------------------------------------------------------------------
    # Cache short-circuit: same file + same JD -> render from resume_json.
    # ------------------------------------------------------------------
    cached = analysis.resume_json or {}
    meta = cached.get("_meta") or {}
    cache_key = build_cache_key(pdf_bytes, job_description)

    if meta.get("cache_key") == cache_key:
        logger.info("analyze_resume: cache HIT")
        context = context_from_payload(cached)
        # Include cached AI results from the model
        context["ai_explanation"] = analysis.ai_explanation
        context["ai_rewrite"] = analysis.ai_rewrite
        return render(
            request,
            "resume/analysis.html",
            {**context, "resume": resume, "analysis": analysis},
        )
    logger.info("analyze_resume: cache MISS")

    # ------------------------------------------------------------------
    # Cache miss: run the full pipeline once and persist the results.
    # ------------------------------------------------------------------
    logger.info("analyze_resume: run_analysis_pipeline start")
    try:
        context, payload = run_analysis_pipeline(pdf_bytes, job_description)
    except Exception:
        logger.exception("Analysis failed for resume id=%s", resume_id)
        messages.error(
            request,
            "Could not analyze this PDF. It may be corrupted or scanned "
            "without an extractable text layer.",
        )
        return redirect("resume_history")
    logger.info("analyze_resume: run_analysis_pipeline end")

    ats = payload["ats"]
    job = payload["job"]

    analysis.ats_score = ats["ats_score"]
    analysis.job_match_score = job["job_fit_score"]
    analysis.recommendations = ats["recommendations"]
    analysis.strengths = ats["strengths"]
    analysis.improvement_areas = ats["improvements"]
    analysis.resume_json = payload
    analysis.save()
    logger.info("analyze_resume: analysis saved id=%s", analysis.id)

    # Call AI service for explanation and rewrite (async-style, but sync here)
    ai_service = get_ai_service()
    logger.info("analyze_resume: AI service enabled=%s", ai_service._enabled)
    ai_explanation = None
    ai_rewrite = None
    if ai_service._enabled:
        # Use cached or fresh results
        logger.info("analyze_resume: ai_service.explain start")
        ai_explanation = ai_service.explain(ats, job, payload["text"])
        logger.info("analyze_resume: ai_service.explain end result=%s", ai_explanation is not None)

        logger.info("analyze_resume: ai_service.rewrite start")
        ai_rewrite = ai_service.rewrite(ats, job, payload["text"])
        logger.info("analyze_resume: ai_service.rewrite end result=%s", ai_rewrite is not None)

        # Cache results on the analysis model for future renders
        if ai_explanation:
            analysis.ai_explanation = ai_explanation.model_dump(mode="json")
        if ai_rewrite:
            analysis.ai_rewrite = ai_rewrite.model_dump(mode="json")
        if ai_explanation or ai_rewrite:
            analysis.save(update_fields=["ai_explanation", "ai_rewrite"])
            logger.info("analyze_resume: AI results cached on analysis model")

    # Include AI results in context
    context["ai_explanation"] = ai_explanation
    context["ai_rewrite"] = ai_rewrite

    logger.info("analyze_resume: rendering template")
    return render(
        request,
        "resume/analysis.html",
        {**context, "resume": resume, "analysis": analysis},
    )


def _delete_storage_file(field_file):
    """Best-effort removal of a FileField's stored file (local or Cloudinary)."""
    if not field_file:
        return
    try:
        if field_file.storage.exists(field_file.name):
            field_file.storage.delete(field_file.name)
    except Exception:
        logger.exception("Failed to delete stored file: %s", field_file.name)


@login_required
def delete_resume(request, resume_id):
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user,
    )

    # Delete the uploaded PDF and job image from storage (local disk or
    # Cloudinary) before removing the rows.
    _delete_storage_file(resume.file)

    if hasattr(resume, "analysis"):
        _delete_storage_file(resume.analysis.job_image)
        resume.analysis.delete()

    resume.delete()

    messages.success(
        request,
        "Resume deleted successfully.",
    )

    return redirect(
        "resume_history",
    )