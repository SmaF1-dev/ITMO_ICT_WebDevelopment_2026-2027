
from django.urls import path

from . import views


app_name = "flights"

urlpatterns = [
    path(
        "",
        views.FlightListView.as_view(),
        name="flight_list",
    ),

    path(
        "reservations/",
        views.my_reservations,
        name="my_reservations",
    ),

    path(
        "reservations/<int:pk>/edit/",
        views.reservation_update,
        name="reservation_update",
    ),

    path(
        "reservations/<int:pk>/delete/",
        views.reservation_delete,
        name="reservation_delete",
    ),

    path(
        "<int:pk>/reserve/",
        views.reservation_create,
        name="reservation_create",
    ),

    path(
        "<int:pk>/",
        views.FlightDetailView.as_view(),
        name="flight_detail",
    ),
]
