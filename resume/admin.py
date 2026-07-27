from django.contrib import admin

from .models import Resume, ResumeAnalysis


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):

    list_display = (
        "title",
        "user",
        "uploaded_at",
    )

    search_fields = (
        "title",
        "user__username",
    )


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):

    list_display = (
        "resume",
        "ats_score",
        "job_match_score",
        "analyzed_at",
    )

    search_fields = (
        "resume__title",
    )