"""
API routing, mounted at /api/ in the project urls.

All endpoints are JWT-authenticated JSON endpoints. Session auth powers the
server-rendered app on separate routes; these never overlap.
"""
from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from account_manager.api_views import (
    LoginTokenObtainPairView,
    logout,
    me,
    profile,
    register,
)
from dashboard.api_views import DashboardView
from resume.api_views import (
    HistoryView,
    ResumeAnalysisView,
    ResumeDetailView,
    ResumeListCreateView,
)

urlpatterns = [
    # ── Auth ───────────────────────────────────────────────────────────
    path("auth/register/", register, name="api-register"),
    path("auth/login/", LoginTokenObtainPairView, name="api-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("auth/me/", me, name="api-me"),
    path("auth/logout/", logout, name="api-logout"),

    # ── Resumes ────────────────────────────────────────────────────────
    path("resumes/", ResumeListCreateView.as_view(), name="api-resume-list"),
    path(
        "resumes/<int:pk>/",
        ResumeDetailView.as_view(),
        name="api-resume-detail",
    ),
    path(
        "resumes/<int:pk>/analysis/",
        ResumeAnalysisView.as_view(),
        name="api-resume-analysis",
    ),

    # ── History / dashboard / profile ──────────────────────────────────
    path("history/", HistoryView.as_view(), name="api-history"),
    path("dashboard/", DashboardView.as_view(), name="api-dashboard"),
    path("profile/", profile, name="api-profile"),
]