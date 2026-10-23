
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Flight, Reservation


User = get_user_model()


class FlightPageTests(TestCase):
    """Проверки пользовательских страниц авиарейсов."""

    def setUp(self):
        departure = timezone.now() + timedelta(days=5)

        self.flight = Flight.objects.create(
            flight_number="SU1234",
            airline="Аэрофлот",
            departure_airport="Санкт-Петербург (LED)",
            arrival_airport="Москва (SVO)",
            departure_time=departure,
            arrival_time=departure + timedelta(hours=2),
            flight_type=Flight.FlightType.DEPARTURE,
            gate="A12",
            seat_capacity=180,
        )

    def test_home_redirects_to_flights(self):
        """Главная страница перенаправляет на табло."""

        response = self.client.get("/")

        self.assertRedirects(
            response,
            reverse("flights:flight_list"),
        )

    def test_flight_list(self):
        """Табло отображает существующие рейсы."""

        response = self.client.get(
            reverse("flights:flight_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SU1234")
        self.assertContains(response, "Аэрофлот")
        self.assertContains(response, "Санкт-Петербург")

    def test_flight_detail(self):
        """Детальная страница содержит информацию о рейсе."""

        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SU1234")
        self.assertContains(response, "A12")
        self.assertContains(response, "180")

    def test_available_seats(self):
        """Количество свободных мест учитывает бронирования."""

        user = User.objects.create_user(
            username="passenger",
            password="StrongTestPassword!2026",
        )

        Reservation.objects.create(
            user=user,
            flight=self.flight,
            seat_number=12,
        )

        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "179")
        self.assertContains(response, "Забронировано")

    def test_missing_flight_returns_404(self):
        """Несуществующий рейс возвращает HTTP 404."""

        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": 99999},
            )
        )

        self.assertEqual(response.status_code, 404)
