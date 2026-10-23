
from django.db.models import Count, F
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Flight


def flights_with_availability():
    """Возвращает рейсы с количеством занятых и свободных мест."""
    return Flight.objects.annotate(
        reserved_seats=Count("reservations"),
        free_seats=F("seat_capacity") - Count("reservations"),
    )


class FlightListView(ListView):
    """Табло со всеми авиарейсами."""

    template_engine = "jinja2"
    template_name = "flights/flight_list.jinja"
    context_object_name = "flights"

    def get_queryset(self):
        return flights_with_availability().order_by(
            "departure_time",
            "flight_number",
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


class FlightDetailView(DetailView):
    """Подробная информация об одном рейсе."""

    template_engine = "jinja2"
    template_name = "flights/flight_detail.jinja"
    context_object_name = "flight"

    def get_queryset(self):
        return flights_with_availability()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context
