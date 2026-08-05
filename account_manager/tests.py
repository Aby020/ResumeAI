"""
Integration tests for the authentication and profile flows.

These exercise the full request/response stack (forms -> views -> templates).
Templates render static assets through {% static %}, so the hashed-manifest
storage is swapped for the plain one (tests never run collectstatic).
"""
from django.contrib.auth.models import User
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
class AuthFlowTests(TestCase):

    def test_login_page_renders_for_anonymous(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login")

    def test_register_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("register"),
            {
                "first_name": "Test User",
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "TestPass123!",
                "confirm_password": "TestPass123!",
            },
        )
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertTrue(user.check_password("TestPass123!"))

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("register"),
            {
                "first_name": "Test User",
                "username": "newuser2",
                "email": "newuser2@example.com",
                "password": "TestPass123!",
                "confirm_password": "Different123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser2").exists())

    def test_login_logout_flow(self):
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="TestPass123!",
        )
        self.assertTrue(self.client.login(username="alice", password="TestPass123!"))

        # Authenticated app pages render after login.
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("resume_history")).status_code, 200)

        # Logout clears the session and lands on the home page.
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_redirects_anonymous_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_profile_renders(self):
        self.client.force_login(
            User.objects.create_user(username="bob", password="TestPass123!")
        )
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profile")

    def test_password_reset_page_renders(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
