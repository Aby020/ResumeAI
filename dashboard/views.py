from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
from django.shortcuts import render

from resume.models import Resume, ResumeAnalysis


@login_required
def dashboard(request):
    resumes = Resume.objects.filter(user=request.user).order_by("-uploaded_at")

    analyses = ResumeAnalysis.objects.filter(resume__user=request.user)

    total_resumes = resumes.count()

    average_ats = analyses.aggregate(Avg("ats_score"))["ats_score__avg"] or 0

    highest_ats = analyses.aggregate(Max("ats_score"))["ats_score__max"] or 0

    best_job_match = (
        analyses.aggregate(Max("job_match_score"))["job_match_score__max"] or 0
    )

    latest_resume = resumes.first()

    recent_resumes = []

    for resume in resumes[:5]:
        analysis = getattr(resume, "analysis", None)

        recent_resumes.append(
            {
                "id": resume.id,
                "title": resume.title,
                "uploaded_at": resume.uploaded_at,
                "ats_score": analysis.ats_score if analysis else 0,
                "job_match_score": analysis.job_match_score if analysis else None,
            }
        )
       

    context = {
        "user": request.user,
        "total_resumes": total_resumes,
        "average_ats": round(average_ats),
        "highest_ats": highest_ats,
        "best_job_match": best_job_match,
        "latest_resume": latest_resume,
        "recent_resumes": recent_resumes,
    }

    return render(request, "dashboard/index.html", context)
