from django import forms

from .models import Reservation, Review


class ReservationSeatForm(forms.ModelForm):
    """Форма выбора свободного места на рейсе."""

    seat_number = forms.TypedChoiceField(
        label="Номер места",
        coerce=int,
        empty_value=None,
        choices=(),
        error_messages={
            "required": "Выберите место.",
            "invalid_choice": (
                "Это место недоступно. Обновите страницу "
                "и выберите другое."
            ),
        },
    )

    class Meta:
        model = Reservation
        fields = ("seat_number",)

    def __init__(self, *args, flight, **kwargs):
        super().__init__(*args, **kwargs)

        self.flight = flight

        occupied = set(
            Reservation.objects.filter(
                flight=flight,
            )
            .exclude(pk=self.instance.pk)
            .values_list("seat_number", flat=True)
        )

        available = [
            number
            for number in range(1, flight.seat_capacity + 1)
            if number not in occupied
        ]

        self.fields["seat_number"].choices = [
            ("", "Выберите свободное место"),
            *[
                (number, f"Место {number}")
                for number in available
            ],
        ]


class ReviewForm(forms.ModelForm):
    """Форма создания и редактирования отзыва о рейсе."""

    rating = forms.TypedChoiceField(
        label="Оценка",
        coerce=int,
        choices=[
            ("", "Выберите оценку"),
            *[
                (score, f"{score} / 10")
                for score in range(1, 11)
            ],
        ],
    )

    class Meta:
        model = Review
        fields = ("rating", "text")

        labels = {
            "text": "Текст отзыва",
        }

        widgets = {
            "text": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": (
                        "Расскажите о впечатлениях от рейса..."
                    ),
                }
            ),
        }