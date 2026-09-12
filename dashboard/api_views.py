"""
DRF API view for the dashboard summary.
"""
from django.db.models import Avg, Max

from rest_framework.response import Response
from rest_framework.views import APIView

from resume.models import Resume

from .serializers import DashboardSerializer


class DashboardView(APIView):
    """``GET /api/dashboard/`` — summary stats for the authenticated user.

    The metrics are recomputed with the same aggregates as
    ``dashboard.views.dashboard``: one query for the resume list (JOINed with
    analysis), one aggregate for the three statistics, and the five newest
    resumes for the recent list.
    """

    def get(self, request):
        resumes = (
            Resume.objects.filter(user=request.user)
            .select_related("analysis")
            .order_by("-uploaded_at")
        )

        total_resumes = resumes.count()

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

        data = {
            "total_resumes": total_resumes,
            "average_ats": round(stats["average_ats"] or 0),
            "highest_ats": stats["highest_ats"] or 0,
            "best_job_match": stats["best_job_match"] or 0,
            "recent_resumes": recent_resumes,
        }

        return Response(DashboardSerializer(data).data)