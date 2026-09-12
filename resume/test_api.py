"""
API tests for resume upload / list / detail / analysis / history.

Every request is JWT-authenticated. Ownership is exercised throughout: a
foreign resume id yields a 404 (never 403 or data), and delete removes the
stored file plus the analysis row. Analysis network calls are avoided by
patching ``get_ai_service`` to a disabled stub.
"""
import os
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from resume.models import Resume, ResumeAnalysis
from resume.services import build_cache_key

from .tests import _minimal_payload, make_pdf


class ResumeApiTests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_dir = tempfile.mkdtemp(prefix="resume_api_test_media_")
        cls._media_override = override_settings(
            MEDIA_ROOT=cls._media_dir,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
                },
            },
        )
        cls._media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._media_override.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            password="pass12345",
        )
        self._auth_as(self.user)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _auth_as(self, user):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}",
        )

    def _upload(self, title="My Resume", filename="resume.pdf", content=None, **extra):
        pdf = content if content is not None else make_pdf()
        payload = {
            "title": title,
            "file": SimpleUploadedFile(
                filename,
                pdf,
                content_type="application/pdf",
            ),
        }
        payload.update(extra)
        return self.client.post(reverse("api-resume-list"), payload, format="multipart")

    def _create_resume_for(self, user, filename="foreign.pdf", title="Foreign", content=None):
        return Resume.objects.create(
            user=user,
            title=title,
            file=SimpleUploadedFile(
                filename,
                content if content is not None else make_pdf(),
                content_type="application/pdf",
            ),
        )

    # ------------------------------------------------------------------
    # Auth gating
    # ------------------------------------------------------------------
    def test_unauthenticated_list_is_401(self):
        self.client.credentials()  # drop the token
        response = self.client.get(reverse("api-resume-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_upload_is_401(self):
        self.client.credentials()
        response = self.client.post(reverse("api-resume-list"), {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ------------------------------------------------------------------
    # List / create
    # ------------------------------------------------------------------
    def test_list_returns_own_resumes_newest_first(self):
        first = self._upload(title="Old").data["id"]
        second = self._upload(title="New").data["id"]
        response = self.client.get(reverse("api-resume-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [r["id"] for r in response.data]
        self.assertEqual(ids, [second, first])

    def test_upload_creates_resume_and_analysis(self):
        response = self._upload()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = response.data
        self.assertIn("id", body)
        self.assertEqual(body["title"], "My Resume")
        self.assertIn("file", body)
        self.assertIn("ats_score", body)
        self.assertTrue(
            Resume.objects.filter(id=body["id"], user=self.user).exists()
        )
        self.assertTrue(
            ResumeAnalysis.objects.filter(resume_id=body["id"]).exists()
        )

    def test_upload_missing_file_is_400(self):
        response = self.client.post(
            reverse("api-resume-list"),
            {"title": "No file"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_upload_non_pdf_is_400(self):
        response = self._upload(filename="resume.txt", content=b"not a pdf")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_upload_empty_file_is_400(self):
        response = self._upload(content=b"")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    # ------------------------------------------------------------------
    # Detail / ownership
    # ------------------------------------------------------------------
    def test_detail_own_resume_is_200(self):
        resume_id = self._upload(title="Mine").data["id"]
        response = self.client.get(
            reverse("api-resume-detail", args=[resume_id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], resume_id)

    def test_detail_other_users_resume_is_404(self):
        other = User.objects.create_user(username="other", password="pass12345")
        foreign = self._create_resume_for(other)
        response = self.client.get(
            reverse("api-resume-detail", args=[foreign.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------
    def test_delete_own_resume_removes_rows_and_file(self):
        resume_id = self._upload(title="Gone", filename="to_delete.pdf").data["id"]
        stored_path = Resume.objects.get(id=resume_id).file.path
        self.assertTrue(os.path.exists(stored_path))

        response = self.client.delete(
            reverse("api-resume-detail", args=[resume_id]),
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Resume.objects.filter(id=resume_id).exists())
        self.assertFalse(ResumeAnalysis.objects.filter(resume_id=resume_id).exists())
        self.assertFalse(os.path.exists(stored_path))

    def test_delete_other_users_resume_is_404_and_kept(self):
        other = User.objects.create_user(username="other", password="pass12345")
        foreign = self._create_resume_for(other)
        response = self.client.delete(
            reverse("api-resume-detail", args=[foreign.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Resume.objects.filter(id=foreign.id).exists())

    def test_unauthenticated_delete_is_401(self):
        self.client.credentials()  # drop the token
        response = self.client.delete(
            reverse("api-resume-detail", args=[1]),
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_keeps_db_consistent_when_storage_delete_fails(self):
        """A failed storage delete must not abort the database deletion.

        ``_delete_storage_file`` is best-effort (logs, never re-raises). If the
        stored PDF cannot be removed the API still deletes the analysis + resume
        rows, so the database is never left pointing at a half-deleted record.
        The storage backend itself is patched to fail so the real wrapper is
        what absorbs the error.
        """
        resume_id = self._upload(
            title="Storage fail",
            filename="storage_fail.pdf",
        ).data["id"]

        with patch.object(
            FileSystemStorage,
            "delete",
            side_effect=OSError("storage unavailable"),
        ):
            response = self.client.delete(
                reverse("api-resume-detail", args=[resume_id]),
            )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Resume.objects.filter(id=resume_id).exists())
        self.assertFalse(ResumeAnalysis.objects.filter(resume_id=resume_id).exists())

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    @patch(
        "resume.api_views.get_ai_service",
        return_value=SimpleNamespace(_enabled=False),
    )
    def test_analysis_computes_full_payload(self, _mock_ai):
        resume_id = self._upload(title="Analyze me").data["id"]

        response = self.client.get(
            reverse("api-resume-analysis", args=[resume_id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data["resume_id"], resume_id)
        self.assertIsInstance(data["ats_score"], int)
        self.assertIn("ats_grade", data)
        self.assertIn("ats_breakdown", data)
        self.assertIn("strengths", data)
        self.assertIn("improvement_areas", data)
        self.assertIn("recommendations", data)
        self.assertIn("detected_skills", data)
        self.assertIn("job_match_score", data)
        self.assertIn("matching_skills", data)
        self.assertIsInstance(data["job_match_details"], dict)
        self.assertIn("match_confidence", data["job_match_details"])
        self.assertIn("ai_explanation", data)
        self.assertIn("ai_rewrite", data)
        self.assertIn("analyzed_at", data)

    def test_analysis_cache_hit_skips_pipeline(self):
        resume = self._create_resume_for(
            self.user,
            filename="cached.pdf",
            title="Cached",
        )
        analysis = ResumeAnalysis.objects.create(resume=resume, ats_score=50)
        analysis.resume_json = _minimal_payload(build_cache_key(make_pdf(), ""))
        analysis.save()

        with patch(
            "resume.api_views.run_analysis_pipeline",
            side_effect=AssertionError("pipeline must not run on cache hit"),
        ):
            response = self.client.get(
                reverse("api-resume-analysis", args=[resume.id]),
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ats_score"], 50)

    def test_analysis_missing_file_returns_cached(self):
        resume = self._create_resume_for(
            self.user,
            filename="gone.pdf",
            title="File gone",
        )
        analysis = ResumeAnalysis.objects.create(resume=resume, ats_score=50)
        analysis.resume_json = _minimal_payload(build_cache_key(make_pdf(), ""))
        analysis.save()
        if os.path.exists(resume.file.path):
            os.remove(resume.file.path)

        response = self.client.get(
            reverse("api-resume-analysis", args=[resume.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ats_score"], 50)

    def test_analysis_missing_file_without_cache_is_404(self):
        resume = self._create_resume_for(
            self.user,
            filename="gone2.pdf",
            title="File gone",
        )
        ResumeAnalysis.objects.create(resume=resume)
        if os.path.exists(resume.file.path):
            os.remove(resume.file.path)

        response = self.client.get(
            reverse("api-resume-analysis", args=[resume.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    @patch(
        "resume.api_views.get_ai_service",
        return_value=SimpleNamespace(_enabled=False),
    )
    def test_analysis_corrupt_pdf_is_400_detail(self, _mock_ai):
        resume = self._create_resume_for(
            self.user,
            filename="corrupt.pdf",
            title="Corrupt",
            content=b"not a real pdf",
        )
        response = self.client.get(
            reverse("api-resume-analysis", args=[resume.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    @patch(
        "resume.api_views.get_ai_service",
        return_value=SimpleNamespace(_enabled=False),
    )
    def test_analysis_textless_pdf_is_400_not_a_zero_score(self, _mock_ai):
        """A scanned/textless PDF is a processing failure, never a 0 score.

        Regression guard for the silent-0 bug: a structurally valid PDF with no
        text layer used to score 0/100 across every category and be returned
        (and persisted) as a normal analysis.
        """
        resume = self._create_resume_for(
            self.user,
            filename="textless.pdf",
            title="Scanned",
            content=make_pdf(""),
        )
        response = self.client.get(
            reverse("api-resume-analysis", args=[resume.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)
        # Nothing misleading was persisted: no ats breakdown, no score.
        analysis = ResumeAnalysis.objects.get(resume=resume)
        self.assertEqual(analysis.ats_score, 0)
        self.assertFalse(analysis.resume_json.get("ats"))

    def test_analysis_other_users_resume_is_404(self):
        other = User.objects.create_user(username="other", password="pass12345")
        foreign = self._create_resume_for(other)
        response = self.client.get(
            reverse("api-resume-analysis", args=[foreign.id]),
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------
    def test_history_returns_own_only(self):
        self._upload(title="Mine A")
        self._upload(title="Mine B")
        other = User.objects.create_user(username="other", password="pass12345")
        self._create_resume_for(other, title="Theirs")

        response = self.client.get(reverse("api-history"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = [r["title"] for r in response.data]
        self.assertEqual(titles, ["Mine B", "Mine A"])
        self.assertNotIn("Theirs", titles)