import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ResumeForm
from .models import Resume
from .utils import (
    extract_text,
    detect_skills,
    calculate_ats_score,
)


@login_required
def upload_resume(request):

    if request.method == "POST":

        form = ResumeForm(request.POST, request.FILES)

        if form.is_valid():

            resume = form.save(commit=False)

            resume.user = request.user

            resume.save()

            messages.success(
                request,
                "Resume uploaded successfully!"
            )

            return redirect("resume_history")

    else:

        form = ResumeForm()

    return render(
        request,
        "resume/upload.html",
        {
            "form": form
        }
    )


@login_required
def resume_history(request):

    resumes = Resume.objects.filter(
        user=request.user
    ).order_by("-uploaded_at")

    return render(
        request,
        "resume/history.html",
        {
            "resumes": resumes
        }
    )


@login_required
def delete_resume(request, resume_id):

    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )

    if resume.file:

        if os.path.isfile(resume.file.path):

            os.remove(resume.file.path)

    resume.delete()

    messages.success(
        request,
        "Resume deleted successfully!"
    )

    return redirect("resume_history")


@login_required
def analyze_resume(request, resume_id):

    resume = get_object_or_404(
        Resume,
        id=resume_id,
        user=request.user
    )

    extracted_text = extract_text(
        resume.file.path
    )

    found_skills, missing_skills = detect_skills(
        extracted_text
    )

    ats_score, ats_breakdown, recommendations = calculate_ats_score(
        extracted_text
    )

    context = {

        "resume": resume,

        "text": extracted_text,

        "word_count": len(extracted_text.split()),

        "character_count": len(extracted_text),

        "found_skills": found_skills,

        "missing_skills": missing_skills,

        "ats_score": ats_score,

        "ats_breakdown": ats_breakdown,

        "recommendations": recommendations,

    }

    return render(
        request,
        "resume/analysis.html",
        context
    )