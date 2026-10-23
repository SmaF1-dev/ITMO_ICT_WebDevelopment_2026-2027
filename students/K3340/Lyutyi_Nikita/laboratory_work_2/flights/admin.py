from django.contrib import admin
from django.db.models import Count

from .models import Flight, Reservation, Review


class ReservationInline(admin.TabularInline):
    """Бронирования непосредственно на странице рейса."""

    model = Reservation

    extra = 0

    fields = (
        "user",
        "seat_number",
        "is_checked_in",
        "ticket_number",
    )

    autocomplete_fields = ("user",)

    show_change_link = True


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    """Администрирование авиарейсов."""

    list_display = (
        "flight_number",
        "airline",
        "departure_airport",
        "arrival_airport",
        "departure_time",
        "flight_type",
        "gate",
        "seat_capacity",
        "reservation_count",
    )

    search_fields = (
        "flight_number",
        "airline",
        "departure_airport",
        "arrival_airport",
    )

    list_filter = (
        "flight_type",
        "airline",
    )

    date_hierarchy = "departure_time"

    ordering = ("departure_time",)

    inlines = (ReservationInline,)

    list_per_page = 20

    def get_queryset(self, request):
        queryset = super().get_queryset(request)

        return queryset.annotate(
            reservation_total=Count("reservations")
        )

    @admin.display(
        description="Бронирований",
        ordering="reservation_total",
    )
    def reservation_count(self, obj):
        return obj.reservation_total


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Управление бронированиями и регистрацией пассажиров."""

    list_display = (
        "flight",
        "user",
        "seat_number",
        "is_checked_in",
        "ticket_number",
        "created_at",
    )

    search_fields = (
        "flight__flight_number",
        "user__username",
        "ticket_number",
    )

    list_filter = (
        "is_checked_in",
        "flight__flight_type",
    )

    autocomplete_fields = (
        "flight",
        "user",
    )

    list_select_related = (
        "flight",
        "user",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    list_per_page = 20


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Управление отзывами об авиарейсах."""

    list_display = (
        "flight",
        "author",
        "flight_date",
        "rating",
        "created_at",
    )

    search_fields = (
        "flight__flight_number",
        "author__username",
        "text",
    )

    list_filter = (
        "rating",
        "flight_date",
    )

    autocomplete_fields = (
        "flight",
        "author",
    )

    list_select_related = (
        "flight",
        "author",
    )

    readonly_fields = ("created_at",)

    ordering = ("-created_at",)

    list_per_page = 20