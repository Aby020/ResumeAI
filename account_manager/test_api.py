"""
API tests for the authentication and profile endpoints.

Exercises the JWT flow end-to-end: register -> login (username or email) ->
/me -> logout, plus the profile GET/PATCH surface. Asserts the security
constraints of the task: no password/hash is ever exposed, and privilege
fields can never be modified through the API.
"""
from django.contrib.auth.models import User
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

# Matches the complexity rules in account_manager/forms.py (RegisterForm).
_PASSWORD = "TestPass123!"
_REGISTER_DATA = {
    "first_name": "Test User",
    "username": "testuser",
    "email": "test@example.com",
    "password": _PASSWORD,
    "confirm_password": _PASSWORD,
}


class AuthApiTests(APITestCase):

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _register(self, **overrides):
        data = dict(_REGISTER_DATA)
        data.update(overrides)
        return self.client.post(reverse("api-register"), data, format="json")

    def _create_user(self, username="alice", email="alice@example.com"):
        return User.objects.create_user(
            username=username,
            email=email,
            password=_PASSWORD,
        )

    def _login(self, **overrides):
        data = {"username": "alice", "password": _PASSWORD}
        data.update(overrides)
        return self.client.post(reverse("api-login"), data, format="json")

    def _auth_as(self, user):
        """Log in via the API and attach the access token to the client."""
        response = self.client.post(
            reverse("api-login"),
            {"username": user.username, "password": _PASSWORD},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['access']}",
        )
        return response

    # ------------------------------------------------------------------
    # Register
    # ------------------------------------------------------------------
    def test_register_creates_user_with_hashed_password(self):
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        body = response.data
        self.assertEqual(body["username"], "testuser")
        self.assertEqual(body["email"], "test@example.com")
        self.assertNotIn("password", body)
        self.assertNotIn("confirm_password", body)

        user = User.objects.get(username="testuser")
        self.assertTrue(user.check_password(_PASSWORD))
        self.assertNotEqual(user.password, _PASSWORD)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            username="other",
            email="test@example.com",
            password=_PASSWORD,
        )
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.filter(username="testuser").count(), 0)

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(
            username="testuser",
            email="other@example.com",
            password=_PASSWORD,
        )
        response = self._register()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_rejects_weak_password(self):
        response = self._register(password="short", confirm_password="short")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_register_rejects_mismatched_passwords(self):
        response = self._register(
            password=_PASSWORD,
            confirm_password="OtherPass123!",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_register_ignores_privilege_fields(self):
        response = self._register(is_staff=True, is_superuser=True)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="testuser")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def test_login_returns_access_and_refresh(self):
        self._create_user()
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_accepts_email(self):
        self._create_user()
        response = self._login(username="alice@example.com")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_invalid_credentials_is_401_detail(self):
        self._create_user()
        response = self._login(password="WrongPass1!")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_token_refresh_issues_new_access(self):
        self._create_user()
        refresh = self._login().data["refresh"]
        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    # ------------------------------------------------------------------
    # Me / logout
    # ------------------------------------------------------------------
    def test_me_unauthenticated_is_401(self):
        response = self.client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_safe_user_data(self):
        self._auth_as(self._create_user())
        response = self.client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")
        self.assertIn("email", response.data)
        self.assertNotIn("password", response.data)

    def test_logout_returns_204(self):
        self._auth_as(self._create_user())
        response = self.client.post(reverse("api-logout"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    def test_profile_get_requires_auth(self):
        response = self.client.get(reverse("api-profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_get_returns_user(self):
        self._auth_as(self._create_user())
        response = self.client.get(reverse("api-profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")

    def test_profile_patch_updates_safe_field(self):
        self._auth_as(self._create_user())
        response = self.client.patch(
            reverse("api-profile"),
            {"first_name": "Alicia"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Alicia")
        User.objects.get(username="alice").refresh_from_db()
        self.assertEqual(User.objects.get(username="alice").first_name, "Alicia")

    def test_profile_patch_privilege_field_ignored(self):
        self._auth_as(self._create_user())
        response = self.client.patch(
            reverse("api-profile"),
            {"is_staff": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("is_staff", response.data)
        self.assertFalse(User.objects.get(username="alice").is_staff)

    def test_profile_patch_username_ignored(self):
        self._auth_as(self._create_user())
        response = self.client.patch(
            reverse("api-profile"),
            {"username": "mallory"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")