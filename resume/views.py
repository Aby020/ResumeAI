import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .ats_engine import calculate_ats_score
from .forms import ResumeForm
from .job_matcher import calculate_job_fit
from .models import Resume, ResumeAnalysis
from .utils import (
    detect_skills,
    extract_text,
    resume_statistics,
)


@login_required
def upload_resume(request):
    if request.method == "POST":
        form = ResumeForm(request.POST, request.FILES)

        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.save()

            # Always create a fresh analysis for every upload
            analysis = ResumeAnalysis.objects.create(
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

    # -----------------------------
    # Extract Resume Text
    # -----------------------------
    if not resume.file:
        messages.error(
            request,
            "Resume file not found. It may have been removed after a server restart. Please upload the resume again.",
        )
        return redirect("upload_resume")

    resume_text = extract_text(
        resume.file,
    )
    print("Resume text length:", len(resume_text))
    print(resume_text[:500])

    # -----------------------------
    # Detect Resume Skills
    # -----------------------------
    found_skills, missing_skills = detect_skills(
        resume_text,
    )

    # -----------------------------
    # ATS Analysis
    # -----------------------------
    ats = calculate_ats_score(
        resume_text,
    )

    # -----------------------------
    # Job Match Analysis
    # -----------------------------
    job_description = analysis.job_description

    job = calculate_job_fit(
        ats["detected_skills"],
        job_description,
    )

    # -----------------------------
    # Save Analysis
    # -----------------------------
    analysis.ats_score = ats["ats_score"]

    analysis.job_match_score = (
        job["job_fit_score"] if job["job_fit_score"] is not None else None
    )

    analysis.recommendations = ats["recommendations"]

    analysis.strengths = ats["strengths"]

    analysis.improvement_areas = ats["improvements"]

    analysis.save()

    # -----------------------------
    # Resume Statistics
    # -----------------------------
    stats = resume_statistics(
        resume_text,
    )

    # -----------------------------
    # Progress Bar Percentages
    # -----------------------------
    ATS_MAX = {
        "Contact Information": 10,
        "Professional Summary": 10,
        "Skills": 20,
        "Experience": 20,
        "Education": 15,
        "Projects": 15,
        "Resume Length": 5,
        "Formatting": 5,
    }

    ats_breakdown_progress = []

    for category, score in ats["breakdown"].items():
        maximum = ATS_MAX.get(
            category,
            20,
        )
        percent = round(
            (score / maximum) * 100,
        )

        ats_breakdown_progress.append(
            {
                "category": category,
                "score": score,
                "percent": percent,
            }
        )

    # -----------------------------
    # Context
    # -----------------------------
    context = {
        "resume": resume,
        "analysis": analysis,
        "text": resume_text,
        "word_count": stats["word_count"],
        "character_count": stats["character_count"],
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        # ATS
        "ats_score": ats["ats_score"],
        "grade": ats["grade"],
        "ats_breakdown": ats_breakdown_progress,
        "strengths": ats["strengths"],
        "improvements": ats["improvements"],
        "recommendations": ats["recommendations"],
        # Job Match
        "job_fit_score": job["job_fit_score"],
        "matching_skills": job["matching_skills"],
        "job_missing_skills": job["missing_skills"],
        "extra_skills": job["extra_skills"],
        "job_recommendations": job["recommendations"],
    }

    return render(
        request,
        "resume/analysis.html",
        context,
    )


@login_required
def delete_resume(request, resume_id):
    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user,
    )

    # Delete uploaded PDF
    try:
        if resume.file and os.path.isfile(
            resume.file.url,
        ):
            os.remove(
                resume.file.url,
            )
    except Exception:
        pass

    # Delete uploaded job image
    try:
        if hasattr(
            resume,
            "analysis",
        ):
            if resume.analysis.job_image and os.path.isfile(
                resume.analysis.job_image.path,
            ):
                os.remove(
                    resume.analysis.job_image.path,
                )
    except Exception:
        pass

    # Delete analysis completely
    if hasattr(
        resume,
        "analysis",
    ):
        resume.analysis.delete()

    # Delete resume permanently
    resume.delete()

    messages.success(
        request,
        "Resume deleted successfully.",
    )

    return redirect(
        "resume_history",
    )
