from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm


class RegisterForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Password"
            }
        )
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Confirm Password"
            }
        )
    )

    class Meta:

        model = User

        fields = [
            "first_name",
            "username",
            "email",
            "password"
        ]

        widgets = {

            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "placeholder": "Full Name"
                }
            ),

            "username": forms.TextInput(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "placeholder": "Username"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control bg-dark text-white border-secondary",
                    "placeholder": "Email"
                }
            )

        }

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")

        confirm = cleaned_data.get("confirm_password")

        if password != confirm:

            raise forms.ValidationError(
                "Passwords do not match."
            )

        return cleaned_data


class LoginForm(AuthenticationForm):

    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Username"
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control bg-dark text-white border-secondary",
                "placeholder": "Password"
            }
        )
    )