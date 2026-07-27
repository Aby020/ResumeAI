from django.urls import path
from . import views

urlpatterns = [

    path(
        "upload/",
        views.upload_resume,
        name="upload_resume"
    ),

    path(
        "history/",
        views.resume_history,
        name="resume_history"
    ),

    path(
        "delete/<int:resume_id>/",
        views.delete_resume,
        name="delete_resume"
    ),

]