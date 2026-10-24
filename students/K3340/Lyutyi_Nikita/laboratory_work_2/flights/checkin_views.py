from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods

from .checkin_forms import CheckInForm
from .models import Flight, Reservation


def staff_access_allowed(request):
    """Проверяет, что пользователь является активным сотрудником."""
    return request.user.is_active and request.user.is_staff


@login_required
@require_GET
def check_in_list(request):
    """Список бронирований для сотрудников аэропорта."""

    if not staff_access_allowed(request):
        return HttpResponseForbidden(
            "Раздел доступен только сотрудникам."
        )

    query = request.GET.get("q", "").strip()[:100]

    reservations = (
        Reservation.objects
        .select_related("user", "flight")
        .order_by(
            "flight__departure_time",
            "seat_number",
            "pk",
        )
    )

    if query:
        reservations = reservations.filter(
            Q(user__username__icontains=query)
            | Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(flight__flight_number__icontains=query)
            | Q(ticket_number__icontains=query)
        )

    return render(
        request,
        "flights/checkin_list.jinja",
        {
            "reservations": reservations,
            "query": query,
            "now": timezone.now(),
        },
        using="jinja2",
    )


@login_required
@require_http_methods(["GET", "POST"])
def check_in_detail(request, pk):
    """Регистрирует пассажира и назначает номер билета."""

    if not staff_access_allowed(request):
        return HttpResponseForbidden(
            "Регистрация доступна только сотрудникам."
        )

    reservation = get_object_or_404(
        Reservation.objects.select_related("user", "flight"),
        pk=pk,
    )

    if reservation.is_checked_in:
        return HttpResponseForbidden(
            "Этот пассажир уже зарегистрирован."
        )

    if reservation.flight.departure_time <= timezone.now():
        return HttpResponseForbidden(
            "Регистрация после отправления рейса недоступна."
        )

    form = CheckInForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                locked_flight = get_object_or_404(
                    Flight.objects.select_for_update(),
                    pk=reservation.flight_id,
                )

                locked_reservation = get_object_or_404(
                    Reservation.objects.select_for_update(),
                    pk=pk,
                )

                if locked_reservation.is_checked_in:
                    return HttpResponseForbidden(
                        "Пассажир уже зарегистрирован."
                    )

                if locked_flight.departure_time <= timezone.now():
                    return HttpResponseForbidden(
                        "Регистрация на рейс закрыта."
                    )

                locked_reservation.ticket_number = (
                    form.cleaned_data["ticket_number"]
                )
                locked_reservation.is_checked_in = True

                locked_reservation.full_clean()

                locked_reservation.save(
                    update_fields=[
                        "ticket_number",
                        "is_checked_in",
                    ]
                )

        except ValidationError as exc:
            form.add_error(
                "ticket_number",
                "; ".join(exc.messages),
            )

        except IntegrityError:
            form.add_error(
                "ticket_number",
                "Номер билета уже используется.",
            )

        else:
            return redirect("flights:check_in_list")

    return render(
        request,
        "flights/checkin_form.jinja",
        {
            "form": form,
            "reservation": reservation,
        },
        using="jinja2",
    )