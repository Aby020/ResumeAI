from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import reverse_lazy

from .forms import RegisterForm, LoginForm


class UserLoginView(LoginView):

    template_name = "account/login.html"

    authentication_form = LoginForm

    redirect_authenticated_user = True

    def get_success_url(self):

        if self.request.user.is_staff:

            return reverse_lazy("dashboard")

        return reverse_lazy("dashboard")


def register(request):

    if request.user.is_authenticated:

        return redirect("dashboard")

    form = RegisterForm()

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            user = form.save(commit=False)

            user.set_password(
                form.cleaned_data["password"]
            )

            user.save()

            login(request, user)

            messages.success(
                request,
                "Welcome to ResumeAI!"
            )

            return redirect("dashboard")

    return render(
        request,
        "account/register.html",
        {
            "form": form
        }
    )


def user_logout(request):

    logout(request)

    messages.success(
        request,
        "Logged out successfully."
    )

    return redirect("home")


def profile(request):

    return render(
        request,
        "account/profile.html"
    )