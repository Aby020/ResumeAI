from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
from django.shortcuts import render

from resume.models import Resume


@login_required
def dashboard(request):
    # One query: resumes JOINed with their analysis (select_related avoids the
    # previous N+1 access of resume.analysis inside the loop).
    resumes = (
        Resume.objects.filter(user=request.user)
        .select_related("analysis")
        .order_by("-uploaded_at")
    )

    total_resumes = resumes.count()

    # All three stats from a single aggregate query (LEFT JOIN fills NULLs for
    # resumes without an analysis; aggregates ignore NULLs).
    stats = resumes.aggregate(
        average_ats=Avg("analysis__ats_score"),
        highest_ats=Max("analysis__ats_score"),
        best_job_match=Max("analysis__job_match_score"),
    )

    recent_resumes = [
        {
            "id": resume.id,
            "title": resume.title,
            "uploaded_at": resume.uploaded_at,
            "ats_score": resume.analysis.ats_score if resume.analysis else 0,
            "job_match_score": resume.analysis.job_match_score
            if resume.analysis
            else None,
        }
        for resume in resumes[:5]
    ]

    context = {
        "user": request.user,
        "total_resumes": total_resumes,
        "average_ats": round(stats["average_ats"] or 0),
        "highest_ats": stats["highest_ats"] or 0,
        "best_job_match": stats["best_job_match"] or 0,
        "latest_resume": resumes.first(),
        "recent_resumes": recent_resumes,
    }

    return render(request, "dashboard/index.html", context)