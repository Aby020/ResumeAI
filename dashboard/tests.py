"""
Integration tests for the dashboard view (stats aggregation + rendering).
"""
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from resume.models import Resume, ResumeAnalysis


def _pdf():
    # Minimal single-page PDF that pdfplumber can parse (see resume/tests.py).
    content = b"BT /F1 12 Tf 72 720 Td (Dashboard) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF" % (
        len(objects) + 1,
        xref_pos,
    )
    return bytes(out)


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
class DashboardTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="dash", password="TestPass123!")
        self.client.force_login(self.user)

    def _create_analyzed_resume(self, title, ats, job_match):
        resume = Resume.objects.create(
            user=self.user,
            title=title,
            file=SimpleUploadedFile(
                f"{title}.pdf",
                _pdf(),
                content_type="application/pdf",
            ),
        )
        ResumeAnalysis.objects.create(
            resume=resume,
            ats_score=ats,
            job_match_score=job_match,
        )
        return resume

    def test_dashboard_renders_stats_for_authenticated_user(self):
        self._create_analyzed_resume("Resume A", ats=80, job_match=75)
        self._create_analyzed_resume("Resume B", ats=60, job_match=50)

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Resume A")
        self.assertContains(response, "Resume B")
        # Average of 80 & 60 -> 70; highest ATS -> 80; best job match -> 75.
        self.assertContains(response, "70")
        self.assertContains(response, "80")
        self.assertContains(response, "75")

    def test_dashboard_handles_zero_resumes(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
