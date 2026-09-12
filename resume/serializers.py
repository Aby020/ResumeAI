"""
DRF serializers for the resume, analysis, and history endpoints.
"""
from rest_framework import serializers

from .models import Resume, ResumeAnalysis

# ---------------------------------------------------------------------------
# Resume list / detail / create
# ---------------------------------------------------------------------------

class ResumeSerializer(serializers.ModelSerializer):
    """General-purpose resume representation with live analysis data.

    The ``ats_score``, ``job_match_score``, and ``analyzed_at`` values are
    pulled from the linked ``ResumeAnalysis`` (populated eagerly via
    ``select_related("analysis")`` in every list/detail queryset).
    """

    ats_score = serializers.SerializerMethodField()
    job_match_score = serializers.SerializerMethodField()
    analyzed_at = serializers.SerializerMethodField()

    class Meta:
        model = Resume
        fields = (
            "id",
            "title",
            "file",
            "uploaded_at",
            "is_deleted",
            "ats_score",
            "job_match_score",
            "analyzed_at",
        )
        read_only_fields = (
            "id",
            "uploaded_at",
            "is_deleted",
        )

    # ------------------------------------------------------------------
    # Field methods
    # ------------------------------------------------------------------
    def get_ats_score(self, obj):
        analysis = getattr(obj, "analysis", None)
        return analysis.ats_score if analysis else None

    def get_job_match_score(self, obj):
        analysis = getattr(obj, "analysis", None)
        return analysis.job_match_score if analysis else None

    def get_analyzed_at(self, obj):
        analysis = getattr(obj, "analysis", None)
        return analysis.analyzed_at if analysis else None


class ResumeCreateSerializer(serializers.Serializer):
    """Upload: ``title`` + ``file`` (required); ``job_description`` /
    ``job_image`` optional. Mirrors ``ResumeForm`` validation logic."""

    title = serializers.CharField(max_length=100)
    file = serializers.FileField()
    job_description = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
    )
    job_image = serializers.ImageField(
        required=False,
        allow_null=True,
    )

    def validate_file(self, value):
        if value.size == 0:
            raise serializers.ValidationError("The uploaded file is empty.")
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("Only PDF files are supported.")
        if value.size > Resume.MAX_UPLOAD_BYTES:
            raise serializers.ValidationError(
                f"Resume PDFs are limited to {Resume.MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
            )
        return value

    def create(self, validated_data):
        from .models import ResumeAnalysis

        request = self.context["request"]
        job_description = validated_data.pop("job_description", "")
        job_image = validated_data.pop("job_image", None)

        resume = Resume.objects.create(
            user=request.user,
            **validated_data,
        )
        ResumeAnalysis.objects.create(
            resume=resume,
            job_description=job_description,
            job_image=job_image,
        )
        return resume


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

class ResumeHistorySerializer(serializers.Serializer):
    """Compact representation for the history list view."""

    resume_id = serializers.IntegerField(source="id")
    title = serializers.CharField()
    ats_score = serializers.SerializerMethodField()
    job_match_score = serializers.SerializerMethodField()
    analyzed_date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_ats_score(self, obj):
        analysis = getattr(obj, "analysis", None)
        return analysis.ats_score if analysis else 0

    def get_job_match_score(self, obj):
        analysis = getattr(obj, "analysis", None)
        return analysis.job_match_score if analysis else None

    def get_analyzed_date(self, obj):
        analysis = getattr(obj, "analysis", None)
        return analysis.analyzed_at if analysis else None

    def get_status(self, obj):
        analysis = getattr(obj, "analysis", None)
        if analysis and (analysis.resume_json or {}).get("ats"):
            return "analyzed"
        return "pending"


# ---------------------------------------------------------------------------
# Full analysis retrieval
# ---------------------------------------------------------------------------

class ResumeAnalysisSerializer(serializers.ModelSerializer):
    """Expose every analysis field needed by the React frontend.

    Values that live in the ``resume_json`` payload (ATS breakdown, detected
    skills, job-match details) are extracted via ``SerializerMethodField``s
    rather than exposed raw, so the response schema is explicit and stable
    regardless of internal payload changes.
    """

    resume_id = serializers.IntegerField(source="resume.id")
    ats_grade = serializers.SerializerMethodField()
    ats_breakdown = serializers.SerializerMethodField()
    detected_skills = serializers.SerializerMethodField()
    matching_skills = serializers.SerializerMethodField()
    missing_skills = serializers.SerializerMethodField()
    extra_skills = serializers.SerializerMethodField()
    job_match_details = serializers.SerializerMethodField()

    class Meta:
        model = ResumeAnalysis
        fields = (
            "resume_id",
            "ats_score",
            "ats_grade",
            "ats_breakdown",
            "strengths",
            "improvement_areas",
            "recommendations",
            "detected_skills",
            "job_match_score",
            "job_description",
            "matching_skills",
            "missing_skills",
            "extra_skills",
            "job_match_details",
            "ai_explanation",
            "ai_rewrite",
            "analyzed_at",
        )
        read_only_fields = fields

    # ── ATS helpers ──────────────────────────────────────────────────
    def _ats(self, obj):
        return (obj.resume_json or {}).get("ats", {})

    def _job(self, obj):
        return (obj.resume_json or {}).get("job", {})

    def get_ats_grade(self, obj):
        return self._ats(obj).get("grade")

    def get_ats_breakdown(self, obj):
        return self._ats(obj).get("breakdown", {})

    def get_detected_skills(self, obj):
        return self._ats(obj).get("detected_skills", [])

    # ── Job-match helpers ────────────────────────────────────────────
    def get_matching_skills(self, obj):
        return self._job(obj).get("matching_skills", [])

    def get_missing_skills(self, obj):
        return self._job(obj).get("missing_skills", [])

    def get_extra_skills(self, obj):
        return self._job(obj).get("extra_skills", [])

    def get_job_match_details(self, obj):
        job = self._job(obj)
        return {
            "match_confidence": job.get("match_confidence"),
            "missing_required_skills": job.get("missing_required_skills", []),
            "missing_preferred_skills": job.get("missing_preferred_skills", []),
            "missing_experience": job.get("missing_experience", []),
            "missing_certifications": job.get("missing_certifications", []),
            "missing_technologies": job.get("missing_technologies", []),
            "resume_strengths": job.get("resume_strengths", []),
            "resume_weaknesses": job.get("resume_weaknesses", []),
            "suggestions": job.get("suggestions", []),
            "recommendations": job.get("recommendations", []),
        }