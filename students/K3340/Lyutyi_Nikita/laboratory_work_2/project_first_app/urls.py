from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.views.generic import RedirectView

from . import views


app_name = "project_first_app"

urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="project_first_app:car_list",
            permanent=False,
        ),
        name="home",
    ),

    # Owners — FBV
    path(
        "owners/",
        views.owner_list,
        name="owner_list",
    ),
    path(
        "owner/<int:owner_id>/",
        views.owner_detail,
        name="owner_detail",
    ),

    # Cars — CBV
    path(
        "cars/",
        views.CarListView.as_view(),
        name="car_list",
    ),
    path(
        "cars/<int:pk>/",
        views.CarDetailView.as_view(),
        name="car_detail",
    ),
    path(
        "cars/<int:pk>/edit/",
        staff_member_required(
            views.CarUpdateView.as_view()
        ),
        name="car_update",
    ),
]