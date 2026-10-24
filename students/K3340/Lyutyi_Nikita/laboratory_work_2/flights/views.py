
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Count, F
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import ReservationSeatForm
from .models import Flight, Reservation


def flights_with_availability():
    """Рейсы с количеством занятых и свободных мест."""
    return Flight.objects.annotate(
        reserved_seats=Count("reservations"),
        free_seats=F("seat_capacity") - Count("reservations"),
    )


class FlightListView(ListView):
    """Табло авиарейсов."""

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
    """Подробная страница авиарейса."""

    template_engine = "jinja2"
    template_name = "flights/flight_detail.jinja"
    context_object_name = "flight"

    def get_queryset(self):
        return flights_with_availability()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context


@login_required
def my_reservations(request):
    """Список бронирований текущего пользователя."""

    reservations = (
        Reservation.objects
        .filter(user=request.user)
        .select_related("flight")
        .order_by("-created_at")
    )

    return render(
        request,
        "flights/my_reservations.jinja",
        {
            "reservations": reservations,
            "now": timezone.now(),
        },
        using="jinja2",
    )


@login_required
def reservation_create(request, pk):
    """Бронирование свободного места на будущем рейсе."""

    flight = get_object_or_404(Flight, pk=pk)

    if flight.departure_time <= timezone.now():
        return HttpResponseForbidden(
            "Нельзя бронировать место на прошедшем рейсе."
        )

    form = ReservationSeatForm(flight=flight)

    if request.method == "POST":
        try:
            with transaction.atomic():
                locked_flight = get_object_or_404(
                    Flight.objects.select_for_update(),
                    pk=pk,
                )

                if locked_flight.departure_time <= timezone.now():
                    return HttpResponseForbidden(
                        "Бронирование на этот рейс закрыто."
                    )

                form = ReservationSeatForm(
                    request.POST,
                    flight=locked_flight,
                )

                if form.is_valid():
                    reservation = form.save(commit=False)

                    reservation.user = request.user
                    reservation.flight = locked_flight

                    reservation.full_clean()
                    reservation.save()

                    return redirect("flights:my_reservations")

        except IntegrityError:
            form.add_error(
                "seat_number",
                "Место уже занято. Выберите другое.",
            )

    return render(
        request,
        "flights/reservation_form.jinja",
        {
            "form": form,
            "flight": flight,
            "editing": False,
        },
        using="jinja2",
    )


@login_required
def reservation_update(request, pk):
    """Изменение места в собственном бронировании."""

    reservation = get_object_or_404(
        Reservation.objects.select_related("flight"),
        pk=pk,
        user=request.user,
    )

    if reservation.is_checked_in:
        return HttpResponseForbidden(
            "Зарегистрированное бронирование изменять нельзя."
        )

    if reservation.flight.departure_time <= timezone.now():
        return HttpResponseForbidden(
            "Нельзя изменять бронирование прошедшего рейса."
        )

    form = ReservationSeatForm(
        instance=reservation,
        flight=reservation.flight,
    )

    if request.method == "POST":
        try:
            with transaction.atomic():
                locked_flight = Flight.objects.select_for_update().get(
                    pk=reservation.flight_id
                )

                locked_reservation = get_object_or_404(
                    Reservation.objects.select_for_update(),
                    pk=pk,
                    user=request.user,
                )

                if locked_reservation.is_checked_in:
                    return HttpResponseForbidden(
                        "Пассажир уже зарегистрирован на рейс."
                    )

                if locked_flight.departure_time <= timezone.now():
                    return HttpResponseForbidden(
                        "Изменение бронирования закрыто."
                    )

                form = ReservationSeatForm(
                    request.POST,
                    instance=locked_reservation,
                    flight=locked_flight,
                )

                if form.is_valid():
                    form.save()
                    return redirect("flights:my_reservations")

        except IntegrityError:
            form.add_error(
                "seat_number",
                "Место уже занято. Выберите другое.",
            )

    return render(
        request,
        "flights/reservation_form.jinja",
        {
            "form": form,
            "flight": reservation.flight,
            "editing": True,
        },
        using="jinja2",
    )


@login_required
def reservation_delete(request, pk):
    """Отмена собственного незарегистрированного бронирования."""

    reservation = get_object_or_404(
        Reservation.objects.select_related("flight"),
        pk=pk,
        user=request.user,
    )

    if reservation.is_checked_in:
        return HttpResponseForbidden(
            "Зарегистрированное бронирование отменять нельзя."
        )

    if reservation.flight.departure_time <= timezone.now():
        return HttpResponseForbidden(
            "Нельзя отменять бронирование прошедшего рейса."
        )

    if request.method == "POST":
        with transaction.atomic():
            locked_flight = Flight.objects.select_for_update().get(
                pk=reservation.flight_id
            )

            locked_reservation = get_object_or_404(
                Reservation.objects.select_for_update(),
                pk=pk,
                user=request.user,
            )

            if (
                locked_reservation.is_checked_in
                or locked_flight.departure_time <= timezone.now()
            ):
                return HttpResponseForbidden(
                    "Отмена этого бронирования недоступна."
                )

            locked_reservation.delete()

        return redirect("flights:my_reservations")

    return render(
        request,
        "flights/reservation_confirm_delete.jinja",
        {"reservation": reservation},
        using="jinja2",
    )
