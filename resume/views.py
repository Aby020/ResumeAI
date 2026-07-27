import os

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .forms import ResumeForm
from .models import Resume


def upload_resume(request):

    if request.method == "POST":

        form = ResumeForm(request.POST, request.FILES)

        if form.is_valid():

            form.save()

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


def resume_history(request):

    resumes = Resume.objects.all().order_by("-uploaded_at")

    return render(
        request,
        "resume/history.html",
        {
            "resumes": resumes
        }
    )


def delete_resume(request, resume_id):

    resume = get_object_or_404(
        Resume,
        id=resume_id
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