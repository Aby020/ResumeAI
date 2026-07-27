from django.urls import path

from .views import (
    UserLoginView,
    register,
    user_logout,
    profile
)

urlpatterns = [

    path(
        "login/",
        UserLoginView.as_view(),
        name="login"
    ),

    path(
        "register/",
        register,
        name="register"
    ),

    path(
        "logout/",
        user_logout,
        name="logout"
    ),

    path(
        "profile/",
        profile,
        name="profile"
    ),

]