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
    path(
        "owners/new/",
        views.owner_create,
        name="owner_create",
    ),

    # Cars — CBV
    path(
        "cars/",
        views.CarListView.as_view(),
        name="car_list",
    ),
    path(
        "cars/new/",
        staff_member_required(
            views.CarCreateView.as_view()
        ),
        name="car_create",
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
    path(
        "cars/<int:pk>/delete/",
        staff_member_required(
            views.CarDeleteView.as_view()
        ),
        name="car_delete",
    ),
]