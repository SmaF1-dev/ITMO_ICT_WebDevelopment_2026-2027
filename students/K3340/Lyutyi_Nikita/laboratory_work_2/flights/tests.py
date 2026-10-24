
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Flight, Reservation


User = get_user_model()


class FlightPageTests(TestCase):
    """Тесты табло, рейсов и бронирований."""

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

        self.user = User.objects.create_user(
            username="passenger",
            password="StrongTestPassword!2026",
        )

        self.other_user = User.objects.create_user(
            username="other_passenger",
            password="AnotherStrongPassword!2026",
        )

    def make_reservation(
        self,
        user=None,
        seat_number=12,
        **kwargs,
    ):
        """Создаёт демонстрационное бронирование."""

        return Reservation.objects.create(
            user=user or self.user,
            flight=self.flight,
            seat_number=seat_number,
            **kwargs,
        )

    # Страницы рейсов

    def test_home_redirects_to_flights(self):
        response = self.client.get("/")

        self.assertRedirects(
            response,
            reverse("flights:flight_list"),
        )

    def test_flight_list(self):
        response = self.client.get(
            reverse("flights:flight_list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SU1234")
        self.assertContains(response, "Аэрофлот")

    def test_flight_detail(self):
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
        self.make_reservation()

        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "179")

    def test_missing_flight_returns_404(self):
        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": 99999},
            )
        )

        self.assertEqual(response.status_code, 404)

    # Создание бронирования

    def test_reservation_requires_login(self):
        reservation_url = reverse(
            "flights:reservation_create",
            kwargs={"pk": self.flight.pk},
        )

        response = self.client.get(reservation_url)

        self.assertRedirects(
            response,
            reverse("accounts:login")
            + "?next="
            + reservation_url,
        )

    def test_create_reservation(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:reservation_create",
                kwargs={"pk": self.flight.pk},
            ),
            {"seat_number": "14"},
        )

        self.assertRedirects(
            response,
            reverse("flights:my_reservations"),
        )

        reservation = Reservation.objects.get(
            user=self.user,
            flight=self.flight,
        )

        self.assertEqual(reservation.seat_number, 14)
        self.assertFalse(reservation.is_checked_in)
        self.assertIsNone(reservation.ticket_number)

    def test_cannot_book_occupied_seat(self):
        self.make_reservation(
            user=self.other_user,
            seat_number=12,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:reservation_create",
                kwargs={"pk": self.flight.pk},
            ),
            {"seat_number": "12"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Reservation.objects.filter(
                user=self.user,
                flight=self.flight,
            ).exists()
        )

        self.assertContains(
            response,
            "Это место недоступно",
        )

    # Изменение бронирования

    def test_edit_own_reservation(self):
        reservation = self.make_reservation(
            seat_number=12,
        )

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:reservation_update",
                kwargs={"pk": reservation.pk},
            ),
            {"seat_number": "15"},
        )

        self.assertRedirects(
            response,
            reverse("flights:my_reservations"),
        )

        reservation.refresh_from_db()

        self.assertEqual(
            reservation.seat_number,
            15,
        )

    # Отмена бронирования

    def test_delete_own_reservation(self):
        reservation = self.make_reservation()

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:reservation_delete",
                kwargs={"pk": reservation.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse("flights:my_reservations"),
        )

        self.assertFalse(
            Reservation.objects.filter(
                pk=reservation.pk,
            ).exists()
        )

    # Проверка доступа

    def test_cannot_modify_another_users_reservation(self):
        reservation = self.make_reservation(
            user=self.other_user,
        )

        self.client.force_login(self.user)

        edit_url = reverse(
            "flights:reservation_update",
            kwargs={"pk": reservation.pk},
        )

        delete_url = reverse(
            "flights:reservation_delete",
            kwargs={"pk": reservation.pk},
        )

        self.assertEqual(
            self.client.get(edit_url).status_code,
            404,
        )

        self.assertEqual(
            self.client.post(edit_url, {
                "seat_number": "20",
            }).status_code,
            404,
        )

        self.assertEqual(
            self.client.post(delete_url).status_code,
            404,
        )

        reservation.refresh_from_db()
        self.assertEqual(reservation.seat_number, 12)

    def test_checked_in_reservation_cannot_be_changed(self):
        reservation = self.make_reservation(
            is_checked_in=True,
            ticket_number="DEMO-TKT-0001",
        )

        self.client.force_login(self.user)

        edit_url = reverse(
            "flights:reservation_update",
            kwargs={"pk": reservation.pk},
        )

        delete_url = reverse(
            "flights:reservation_delete",
            kwargs={"pk": reservation.pk},
        )

        self.assertEqual(
            self.client.get(edit_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.post(delete_url).status_code,
            403,
        )

        self.assertTrue(
            Reservation.objects.filter(
                pk=reservation.pk,
            ).exists()
        )

    def test_past_flight_cannot_be_booked(self):
        departure = timezone.now() - timedelta(days=2)

        past_flight = Flight.objects.create(
            flight_number="PAST100",
            airline="Test Air",
            departure_airport="LED",
            arrival_airport="SVO",
            departure_time=departure,
            arrival_time=departure + timedelta(hours=2),
            flight_type=Flight.FlightType.DEPARTURE,
            seat_capacity=50,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "flights:reservation_create",
                kwargs={"pk": past_flight.pk},
            )
        )

        self.assertEqual(response.status_code, 403)


    def test_my_reservations_shows_only_my_data(self):
        my_reservation = self.make_reservation(
            user=self.user,
            seat_number=12,
        )

        other_reservation = self.make_reservation(
            user=self.other_user,
            seat_number=13,
        )

        self.client.force_login(self.user)

        response = self.client.get(
            reverse("flights:my_reservations")
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            reverse(
                "flights:reservation_update",
                kwargs={"pk": my_reservation.pk},
            ),
        )

        self.assertNotContains(
            response,
            reverse(
                "flights:reservation_update",
                kwargs={"pk": other_reservation.pk},
            ),
        )


    # Ограничение PostgreSQL

    def test_database_rejects_duplicate_seat(self):
        self.make_reservation(
            user=self.user,
            seat_number=12,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.make_reservation(
                    user=self.other_user,
                    seat_number=12,
                )

        self.assertEqual(
            Reservation.objects.count(),
            1,
        )
