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
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user,
        is_deleted=False,
    )

    analysis, created = ResumeAnalysis.objects.get_or_create(
        resume=resume,
    )

    # ------------------------------------------------------------------
    # Read the PDF bytes once. Unreadable files degrade gracefully: render
    # the last cached analysis if one exists, otherwise explain and redirect.
    # ------------------------------------------------------------------
    pdf_bytes = read_file_bytes(resume.file)

    if pdf_bytes is None:
        if analysis.resume_json:
            context = context_from_payload(analysis.resume_json)
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
        context = context_from_payload(cached)
        return render(
            request,
            "resume/analysis.html",
            {**context, "resume": resume, "analysis": analysis},
        )

    # ------------------------------------------------------------------
    # Cache miss: run the full pipeline once and persist the results.
    # ------------------------------------------------------------------
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

    ats = payload["ats"]
    job = payload["job"]

    analysis.ats_score = ats["ats_score"]
    analysis.job_match_score = job["job_fit_score"]
    analysis.recommendations = ats["recommendations"]
    analysis.strengths = ats["strengths"]
    analysis.improvement_areas = ats["improvements"]
    analysis.resume_json = payload
    analysis.save()

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