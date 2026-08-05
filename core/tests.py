"""
Integration tests for the public landing page.
"""
from django.test import TestCase, override_settings
from django.urls import reverse


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
class LandingPageTests(TestCase):

    def test_home_renders_for_anonymous(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ResumeAI")
