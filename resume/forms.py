from django import forms

from .models import Resume


class ResumeForm(forms.ModelForm):

    job_description = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 8,
                "placeholder": "Paste the job description here (Optional)..."
            }
        )
    )

    job_image = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".png,.jpg,.jpeg"
            }
        )
    )

    class Meta:

        model = Resume

        fields = [
            "title",
            "file",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Resume Title"
                }
            ),

            "file": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": ".pdf"
                }
            ),

        }

    def clean_file(self):
        # Mirrors the API serializer's size guard (see Resume.MAX_UPLOAD_BYTES).
        file = self.cleaned_data.get("file")
        if file and file.size > Resume.MAX_UPLOAD_BYTES:
            raise forms.ValidationError(
                f"Resume PDFs are limited to {Resume.MAX_UPLOAD_BYTES // (1024 * 1024)} MB."
            )
        return file
