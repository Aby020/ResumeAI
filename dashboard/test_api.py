"""
API tests for the dashboard summary endpoint.

Metrics must mirror dashboard.views.dashboard: totals, aggregates, and the
five most recent resumes for the authenticated user only.
"""
import shutil
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from resume.models import Resume, ResumeAnalysis

from resume.tests import make_pdf


@override_settings(
    STORAGES={
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
)
class DashboardApiTests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_dir = tempfile.mkdtemp(prefix="dashboard_api_test_media_")
        cls._media_override = override_settings(MEDIA_ROOT=cls._media_dir)
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboard",
            password="pass12345",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(self.user)}",
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _create_analyzed_resume(self, title, ats, match, user=None):
        owner = user or self.user
        resume = Resume.objects.create(
            user=owner,
            title=title,
            file=SimpleUploadedFile(
                f"{title}.pdf",
                make_pdf(),
                content_type="application/pdf",
            ),
        )
        ResumeAnalysis.objects.create(
            resume=resume,
            ats_score=ats,
            job_match_score=match,
            resume_json={"ats": {"ats_score": ats}},
        )
        return resume

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------
    def test_dashboard_reports_aggregates(self):
        self._create_analyzed_resume("R1", 70, 80)
        self._create_analyzed_resume("R2", 90, 60)
        self._create_analyzed_resume("R3", 80, None)  # no job match

        response = self.client.get(reverse("api-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["total_resumes"], 3)
        self.assertEqual(data["highest_ats"], 90)
        self.assertEqual(data["average_ats"], 80)  # (70 + 90 + 80) / 3
        self.assertEqual(data["best_job_match"], 80)
        self.assertEqual(len(data["recent_resumes"]), 3)

    def test_dashboard_handles_zero_resumes(self):
        response = self.client.get(reverse("api-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["total_resumes"], 0)
        self.assertEqual(data["average_ats"], 0)
        self.assertEqual(data["highest_ats"], 0)
        self.assertEqual(data["best_job_match"], 0)
        self.assertEqual(data["recent_resumes"], [])

    def test_dashboard_ignores_other_users_data(self):
        other = User.objects.create_user(username="other", password="pass12345")
        self._create_analyzed_resume("Mine", 50, 50)
        self._create_analyzed_resume("Theirs", 99, 99, user=other)

        response = self.client.get(reverse("api-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["total_resumes"], 1)
        self.assertEqual(data["highest_ats"], 50)
        self.assertEqual(data["best_job_match"], 50)

    def test_dashboard_unauthenticated_is_401(self):
        self.client.credentials()  # drop the token
        response = self.client.get(reverse("api-dashboard"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)