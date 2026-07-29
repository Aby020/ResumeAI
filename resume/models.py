from django.db import models
from django.contrib.auth.models import User


class Resume(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="resumes"
    )

    title = models.CharField(
        max_length=100
    )

    file = models.FileField(
        upload_to="resumes/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    is_deleted = models.BooleanField(
        default=False
    )

    deleted_at = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class ResumeAnalysis(models.Model):

    resume = models.OneToOneField(
        Resume,
        on_delete=models.CASCADE,
        related_name="analysis"
    )

    ats_score = models.PositiveIntegerField(
        default=0
    )

    job_match_score = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    job_description = models.TextField(
        blank=True
    )

    job_image = models.ImageField(
        upload_to="job_descriptions/",
        null=True,
        blank=True
    )

    recommendations = models.JSONField(
        default=list,
        blank=True
    )

    strengths = models.JSONField(
        default=list,
        blank=True
    )

    improvement_areas = models.JSONField(
        default=list,
        blank=True
    )

    analyzed_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Analysis - {self.resume.title}"