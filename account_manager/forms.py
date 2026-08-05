import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import (
    AuthenticationForm,
    SetPasswordForm,
)


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control pe-5",
                "placeholder": "Password",
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control pe-5",
                "placeholder": "Confirm Password",
            }
        )
    )

    class Meta:

        model = User

        fields = ["first_name", "username", "email", "password"]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Full Name",
                }
            ),
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Username",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Email",
                }
            ),
        }

    def clean_password(self):

        password = self.cleaned_data.get("password")

        validate_password(password)

        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Password must contain at least one uppercase letter."
            )

        if not re.search(r"[a-z]", password):
            raise forms.ValidationError(
                "Password must contain at least one lowercase letter."
            )

        if not re.search(r"\d", password):
            raise forms.ValidationError("Password must contain at least one number.")

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise forms.ValidationError(
                "Password must contain at least one special character."
            )

        return password

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if email:
            email = email.strip().lower()

            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(
                    "An account with this email already exists."
                )

        return email

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm = cleaned_data.get("confirm_password")

        if password != confirm:

            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Username",
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Password",
            }
        )
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean(self):

        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:

            try:
                user = User.objects.get(email__iexact=username)
                username = user.username
            except User.DoesNotExist:
                pass

            self.user_cache = authenticate(
                self.request, username=username, password=password
            )

            if self.user_cache is None:
                raise forms.ValidationError("Invalid username/email or password.")

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data
    
class CustomSetPasswordForm(SetPasswordForm):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["new_password1"].widget.attrs.update(
            {
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "New Password",
            }
        )

        self.fields["new_password2"].widget.attrs.update(
            {
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Confirm Password",
            }
        )
