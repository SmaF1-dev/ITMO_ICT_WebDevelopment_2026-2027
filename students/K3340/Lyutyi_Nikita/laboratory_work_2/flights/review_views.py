from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import ReviewForm
from .models import Flight, Reservation, Review
from .views import FlightDetailView


class FlightReviewsDetailView(FlightDetailView):
    """Страница рейса с отзывами и списком пассажиров."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["reviews"] = (
            Review.objects
            .filter(flight=self.object)
            .select_related("author")
            .order_by("-created_at", "-pk")
        )

        context["review_stats"] = (
            Review.objects
            .filter(flight=self.object)
            .aggregate(
                count=Count("pk"),
                average=Avg("rating"),
            )
        )

        context["passengers"] = (
            Reservation.objects
            .filter(flight=self.object)
            .select_related("user")
            .order_by("seat_number")
        )

        if self.request.user.is_authenticated:
            context["my_review"] = (
                Review.objects
                .filter(
                    flight=self.object,
                    author=self.request.user,
                )
                .first()
            )
        else:
            context["my_review"] = None

        return context


@login_required
def review_create(request, pk):
    """Создание отзыва после прибытия авиарейса."""

    flight = get_object_or_404(Flight, pk=pk)

    if flight.arrival_time > timezone.now():
        return HttpResponseForbidden(
            "Отзыв можно оставить после прибытия рейса."
        )

    existing_review = Review.objects.filter(
        flight=flight,
        author=request.user,
    ).first()

    if existing_review is not None:
        return redirect(
            "flights:review_update",
            pk=existing_review.pk,
        )

    form = ReviewForm(
        request.POST if request.method == "POST" else None
    )

    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)

        review.flight = flight
        review.author = request.user
        review.flight_date = timezone.localtime(
            flight.departure_time
        ).date()

        try:
            with transaction.atomic():
                review.save()
        except IntegrityError:
            form.add_error(
                None,
                "Вы уже оставили отзыв об этом рейсе.",
            )
        else:
            return redirect(
                "flights:flight_detail",
                pk=flight.pk,
            )

    return render(
        request,
        "flights/review_form.jinja",
        {
            "form": form,
            "flight": flight,
            "editing": False,
        },
        using="jinja2",
    )


@login_required
def review_update(request, pk):
    """Редактирование собственного отзыва."""

    review = get_object_or_404(
        Review.objects.select_related("flight"),
        pk=pk,
        author=request.user,
    )

    form = ReviewForm(
        request.POST if request.method == "POST" else None,
        instance=review,
    )

    if request.method == "POST" and form.is_valid():
        form.save()

        return redirect(
            "flights:flight_detail",
            pk=review.flight_id,
        )

    return render(
        request,
        "flights/review_form.jinja",
        {
            "form": form,
            "flight": review.flight,
            "editing": True,
        },
        using="jinja2",
    )


@login_required
def review_delete(request, pk):
    """Удаление собственного отзыва после подтверждения."""

    review = get_object_or_404(
        Review.objects.select_related("flight"),
        pk=pk,
        author=request.user,
    )

    if request.method == "POST":
        flight_id = review.flight_id
        review.delete()

        return redirect(
            "flights:flight_detail",
            pk=flight_id,
        )

    return render(
        request,
        "flights/review_confirm_delete.jinja",
        {"review": review},
        using="jinja2",
    )