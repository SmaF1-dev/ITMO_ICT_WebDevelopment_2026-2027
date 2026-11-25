from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Flight, Reservation


User = get_user_model()


class CheckInTests(TestCase):
    """Проверки регистрации пассажиров сотрудниками."""

    def setUp(self):
        password = "StrongTestPassword!2026"

        self.staff = User.objects.create_user(
            username="staff_operator",
            password=password,
            is_staff=True,
        )

        self.passenger = User.objects.create_user(
            username="passenger_alpha",
            password=password,
        )

        self.other_passenger = User.objects.create_user(
            username="passenger_beta",
            password=password,
        )

        departure = timezone.now() + timedelta(days=5)

        self.flight = Flight.objects.create(
            flight_number="CHECK100",
            airline="Учебные авиалинии",
            departure_airport="Санкт-Петербург (LED)",
            arrival_airport="Москва (SVO)",
            departure_time=departure,
            arrival_time=departure + timedelta(hours=2),
            flight_type=Flight.FlightType.DEPARTURE,
            gate="A12",
            seat_capacity=50,
        )

        self.reservation = Reservation.objects.create(
            user=self.passenger,
            flight=self.flight,
            seat_number=12,
        )

        self.other_reservation = Reservation.objects.create(
            user=self.other_passenger,
            flight=self.flight,
            seat_number=13,
        )

        self.list_url = reverse("flights:check_in_list")

        self.detail_url = reverse(
            "flights:check_in_detail",
            kwargs={"pk": self.reservation.pk},
        )

    def test_guest_must_log_in(self):
        """Неавторизованный посетитель не видит раздел."""

        list_response = self.client.get(self.list_url)

        self.assertRedirects(
            list_response,
            reverse("accounts:login")
            + "?next="
            + self.list_url,
        )

        detail_response = self.client.get(self.detail_url)

        self.assertRedirects(
            detail_response,
            reverse("accounts:login")
            + "?next="
            + self.detail_url,
        )

    def test_regular_user_cannot_access_check_in(self):
        """Обычный пользователь не обладает правами сотрудника."""

        self.client.force_login(self.passenger)

        self.assertEqual(
            self.client.get(self.list_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.get(self.detail_url).status_code,
            403,
        )

        response = self.client.post(
            self.detail_url,
            {"ticket_number": "DEMO-TKT-0002"},
        )

        self.assertEqual(response.status_code, 403)

        self.reservation.refresh_from_db()

        self.assertFalse(self.reservation.is_checked_in)
        self.assertIsNone(self.reservation.ticket_number)

    def test_staff_can_view_and_search_reservations(self):
        """Сотрудник видит бронирования и может искать пассажира."""

        self.client.force_login(self.staff)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "passenger_alpha")
        self.assertContains(response, "passenger_beta")
        self.assertContains(response, "CHECK100")

        search_response = self.client.get(
            self.list_url,
            {"q": "passenger_alpha"},
        )

        self.assertEqual(search_response.status_code, 200)
        self.assertContains(search_response, "passenger_alpha")
        self.assertNotContains(search_response, "passenger_beta")

    def test_get_does_not_register_passenger(self):
        """Открытие формы не должно менять бронирование."""

        self.client.force_login(self.staff)

        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CHECK100")
        self.assertContains(response, "passenger_alpha")

        self.reservation.refresh_from_db()

        self.assertFalse(self.reservation.is_checked_in)
        self.assertIsNone(self.reservation.ticket_number)

    def test_staff_can_register_passenger(self):
        """Сотрудник назначает билет и завершает регистрацию."""

        self.client.force_login(self.staff)

        response = self.client.post(
            self.detail_url,
            {
                "ticket_number": "demo-tkt-0002",
            },
        )

        self.assertRedirects(
            response,
            self.list_url,
        )

        self.reservation.refresh_from_db()

        self.assertTrue(self.reservation.is_checked_in)

        self.assertEqual(
            self.reservation.ticket_number,
            "DEMO-TKT-0002",
        )

        self.assertEqual(self.reservation.seat_number, 12)
        self.assertEqual(self.reservation.user, self.passenger)

    def test_duplicate_ticket_number_is_rejected(self):
        """Нельзя назначить номер уже существующего билета."""

        self.other_reservation.ticket_number = "DEMO-TKT-0002"
        self.other_reservation.is_checked_in = True
        self.other_reservation.save()

        self.client.force_login(self.staff)

        response = self.client.post(
            self.detail_url,
            {
                "ticket_number": "DEMO-TKT-0002",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "уже существует",
        )

        self.reservation.refresh_from_db()

        self.assertFalse(self.reservation.is_checked_in)
        self.assertIsNone(self.reservation.ticket_number)

    def test_invalid_ticket_number_is_rejected(self):
        """Номер билета должен соответствовать формату."""

        self.client.force_login(self.staff)

        response = self.client.post(
            self.detail_url,
            {
                "ticket_number": "BAD NUMBER",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            "латинские буквы, цифры и дефисы",
        )

        self.reservation.refresh_from_db()

        self.assertFalse(self.reservation.is_checked_in)
        self.assertIsNone(self.reservation.ticket_number)

    def test_registered_passenger_cannot_be_registered_again(self):
        """Повторная регистрация запрещена."""

        self.reservation.is_checked_in = True
        self.reservation.ticket_number = "DEMO-TKT-0002"
        self.reservation.save()

        self.client.force_login(self.staff)

        self.assertEqual(
            self.client.get(self.detail_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.post(
                self.detail_url,
                {"ticket_number": "DEMO-TKT-9999"},
            ).status_code,
            403,
        )

        self.reservation.refresh_from_db()

        self.assertEqual(
            self.reservation.ticket_number,
            "DEMO-TKT-0002",
        )

    def test_past_flight_cannot_be_checked_in(self):
        """После отправления рейса регистрация закрыта."""

        departure = timezone.now() - timedelta(days=1)

        self.flight.departure_time = departure
        self.flight.arrival_time = departure + timedelta(hours=2)

        self.flight.save(
            update_fields=[
                "departure_time",
                "arrival_time",
            ]
        )

        self.client.force_login(self.staff)

        response = self.client.post(
            self.detail_url,
            {"ticket_number": "DEMO-TKT-0002"},
        )

        self.assertEqual(response.status_code, 403)

        self.reservation.refresh_from_db()

        self.assertFalse(self.reservation.is_checked_in)

    def test_public_passenger_list_hides_ticket_numbers(self):
        """Посетитель видит пассажиров без номеров билетов."""

        self.reservation.is_checked_in = True
        self.reservation.ticket_number = "DEMO-TKT-PRIVATE"
        self.reservation.save()

        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Пассажиры рейса")
        self.assertContains(response, "passenger_alpha")
        self.assertContains(response, "passenger_beta")
        self.assertContains(response, "Зарегистрирован")

        self.assertNotContains(
            response,
            "DEMO-TKT-PRIVATE",
        )

    def test_checked_in_passenger_cannot_change_booking(self):
        """После регистрации пассажир не может изменить бронь."""

        self.client.force_login(self.staff)

        check_in_response = self.client.post(
            self.detail_url,
            {"ticket_number": "DEMO-TKT-0002"},
        )

        self.assertRedirects(
            check_in_response,
            self.list_url,
        )

        self.client.force_login(self.passenger)

        update_url = reverse(
            "flights:reservation_update",
            kwargs={"pk": self.reservation.pk},
        )

        delete_url = reverse(
            "flights:reservation_delete",
            kwargs={"pk": self.reservation.pk},
        )

        self.assertEqual(
            self.client.get(update_url).status_code,
            403,
        )

        self.assertEqual(
            self.client.post(delete_url).status_code,
            403,
        )

        self.reservation.refresh_from_db()

        self.assertTrue(self.reservation.is_checked_in)
        self.assertEqual(self.reservation.seat_number, 12)