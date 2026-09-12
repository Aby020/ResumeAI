"""
DRF serializer for the dashboard summary endpoint.
"""
from rest_framework import serializers


class RecentResumeSerializer(serializers.Serializer):
    """One recent-resume row. Mirrors the dict built in dashboard.views."""

    id = serializers.IntegerField()
    title = serializers.CharField()
    uploaded_at = serializers.DateTimeField()
    ats_score = serializers.IntegerField()
    job_match_score = serializers.IntegerField(allow_null=True)


class DashboardSerializer(serializers.Serializer):
    """Dashboard metrics, mirroring dashboard.views.dashboard exactly.

    No invented metrics: total_resumes, the aggregate ATS/job-match stats, and
    the five most recent resumes are all computed identically to the
    server-rendered dashboard.
    """

    total_resumes = serializers.IntegerField()
    average_ats = serializers.IntegerField()
    highest_ats = serializers.IntegerField()
    best_job_match = serializers.IntegerField()
    recent_resumes = RecentResumeSerializer(many=True)