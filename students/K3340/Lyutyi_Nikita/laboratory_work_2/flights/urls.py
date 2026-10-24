from django.urls import path

from . import checkin_views, review_views, views


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
        "reviews/<int:pk>/edit/",
        review_views.review_update,
        name="review_update",
    ),
    path(
        "reviews/<int:pk>/delete/",
        review_views.review_delete,
        name="review_delete",
    ),
    path(
        "check-in/",
        checkin_views.check_in_list,
        name="check_in_list",
    ),
    path(
        "check-in/<int:pk>/",
        checkin_views.check_in_detail,
        name="check_in_detail",
    ),
    path(
        "<int:pk>/reserve/",
        views.reservation_create,
        name="reservation_create",
    ),
    path(
        "<int:pk>/review/new/",
        review_views.review_create,
        name="review_create",
    ),
    path(
        "<int:pk>/",
        review_views.FlightReviewsDetailView.as_view(),
        name="flight_detail",
    ),
]