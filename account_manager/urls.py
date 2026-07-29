from django.urls import path
from django.contrib.auth import views as auth_views

from .views import UserLoginView, register, user_logout, profile
from .forms import CustomSetPasswordForm

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", register, name="register"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="account/password_reset.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="account/password_reset_done.html",
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="account/password_reset_confirm.html",
            form_class=CustomSetPasswordForm,
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="account/password_reset_complete.html",
        ),
        name="password_reset_complete",
    ),
    path("logout/", user_logout, name="logout"),
    path("profile/", profile, name="profile"),
]
