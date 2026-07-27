from django import forms
from .models import Resume


class ResumeForm(forms.ModelForm):

    class Meta:

        model = Resume

        fields = ["title", "file"]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter Resume Name"
                }
            ),

            "file": forms.FileInput(
                attrs={
                    "class": "form-control"
                }
            ),
        }