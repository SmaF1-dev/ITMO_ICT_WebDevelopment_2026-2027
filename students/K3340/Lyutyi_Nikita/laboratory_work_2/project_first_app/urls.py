from django.urls import path

from . import views


app_name = "project_first_app"

urlpatterns = [
    path(
        "owner/<int:owner_id>/",
        views.owner_detail,
        name="owner_detail",
    ),
]