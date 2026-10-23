from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone


class Flight(models.Model):
    """Авиарейс, отображаемый на информационном табло."""

    class FlightType(models.TextChoices):
        ARRIVAL = "arrival", "Прибытие"
        DEPARTURE = "departure", "Отправление"

    flight_number = models.CharField(
        "Номер рейса",
        max_length=20,
    )

    airline = models.CharField(
        "Авиакомпания",
        max_length=100,
    )

    departure_airport = models.CharField(
        "Аэропорт отправления",
        max_length=100,
    )

    arrival_airport = models.CharField(
        "Аэропорт прибытия",
        max_length=100,
    )

    departure_time = models.DateTimeField(
        "Время отправления",
    )

    arrival_time = models.DateTimeField(
        "Время прибытия",
    )

    flight_type = models.CharField(
        "Тип рейса",
        max_length=10,
        choices=FlightType.choices,
    )

    gate = models.CharField(
        "Выход на посадку",
        max_length=10,
        blank=True,
    )

    seat_capacity = models.PositiveSmallIntegerField(
        "Количество мест",
        default=180,
        validators=[MinValueValidator(1)],
    )

    class Meta:
        ordering = ["departure_time", "flight_number"]

        verbose_name = "Авиарейс"
        verbose_name_plural = "Авиарейсы"

        constraints = [
            models.UniqueConstraint(
                fields=["flight_number", "departure_time"],
                name="unique_flight_departure",
            ),
            models.CheckConstraint(
                check=models.Q(seat_capacity__gte=1),
                name="flight_positive_capacity",
            ),
        ]

    def clean(self):
        super().clean()

        if self.departure_time and self.arrival_time:
            if self.arrival_time <= self.departure_time:
                raise ValidationError({
                    "arrival_time": (
                        "Прибытие должно быть позже отправления."
                    )
                })

        if self.departure_airport and self.arrival_airport:
            if (
                self.departure_airport.strip().casefold()
                == self.arrival_airport.strip().casefold()
            ):
                raise ValidationError({
                    "arrival_airport": (
                        "Аэропорты отправления и прибытия "
                        "должны различаться."
                    )
                })

        if self.pk and self.seat_capacity:
            if self.reservations.filter(
                seat_number__gt=self.seat_capacity
            ).exists():
                raise ValidationError({
                    "seat_capacity": (
                        "Нельзя уменьшить вместимость ниже "
                        "номера уже забронированного места."
                    )
                })

    def __str__(self):
        return (
            f"{self.flight_number}: "
            f"{self.departure_airport} → {self.arrival_airport}"
        )


class Reservation(models.Model):
    """Бронирование конкретного места на авиарейсе."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flight_reservations",
        verbose_name="Пассажир",
    )

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="Рейс",
    )

    seat_number = models.PositiveSmallIntegerField(
        "Номер места",
        validators=[MinValueValidator(1)],
    )

    is_checked_in = models.BooleanField(
        "Зарегистрирован на рейс",
        default=False,
    )

    ticket_number = models.CharField(
        "Номер билета",
        max_length=40,
        unique=True,
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        "Дата бронирования",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["flight", "seat_number"]

        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"

        constraints = [
            models.UniqueConstraint(
                fields=["flight", "seat_number"],
                name="unique_flight_seat",
            ),
            models.CheckConstraint(
                check=models.Q(seat_number__gte=1),
                name="reservation_positive_seat",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(
                        is_checked_in=False,
                        ticket_number__isnull=True,
                    )
                    |
                    (
                        models.Q(
                            is_checked_in=True,
                            ticket_number__isnull=False,
                        )
                        & ~models.Q(ticket_number="")
                    )
                ),
                name="reservation_checkin_ticket",
            ),
        ]

    def clean(self):
        super().clean()

        if self.flight_id and self.seat_number is not None:
            if self.seat_number > self.flight.seat_capacity:
                raise ValidationError({
                    "seat_number": (
                        "Номер места превышает вместимость рейса."
                    )
                })

        if self.is_checked_in and not (
            self.ticket_number and self.ticket_number.strip()
        ):
            raise ValidationError({
                "ticket_number": (
                    "Для регистрации пассажира нужен номер билета."
                )
            })

        if not self.is_checked_in and self.ticket_number:
            raise ValidationError({
                "ticket_number": (
                    "Номер билета указывается только "
                    "для зарегистрированного пассажира."
                )
            })

    def __str__(self):
        return (
            f"{self.user} — {self.flight.flight_number}, "
            f"место {self.seat_number}"
        )


class Review(models.Model):
    """Отзыв пользователя об авиарейсе."""

    flight = models.ForeignKey(
        Flight,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Рейс",
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flight_reviews",
        verbose_name="Автор",
    )

    flight_date = models.DateField(
        "Дата рейса",
    )

    text = models.TextField(
        "Текст отзыва",
    )

    rating = models.PositiveSmallIntegerField(
        "Оценка",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
    )

    created_at = models.DateTimeField(
        "Дата публикации",
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

        constraints = [
            models.UniqueConstraint(
                fields=["flight", "author"],
                name="unique_review_author_flight",
            ),
            models.CheckConstraint(
                check=(
                    models.Q(rating__gte=1)
                    & models.Q(rating__lte=10)
                ),
                name="review_rating_range",
            ),
        ]

    def clean(self):
        super().clean()

        if self.flight_id and self.flight_date:
            scheduled_date = timezone.localtime(
                self.flight.departure_time
            ).date()

            if self.flight_date != scheduled_date:
                raise ValidationError({
                    "flight_date": (
                        "Дата отзыва должна соответствовать "
                        "дате отправления выбранного рейса."
                    )
                })

    def __str__(self):
        return (
            f"Отзыв {self.author} о рейсе "
            f"{self.flight.flight_number}: {self.rating}/10"
        )