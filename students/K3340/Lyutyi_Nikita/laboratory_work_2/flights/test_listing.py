from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Flight, Reservation


User = get_user_model()


class FlightListingTests(TestCase):
    """Проверки поиска, фильтрации, сортировки и страниц табло."""

    def setUp(self):
        now = timezone.now()

        flights_data = [
            (
                "FL101",
                "Аэрофлот",
                "Санкт-Петербург (LED)",
                "Москва (SVO)",
                "departure",
            ),
            (
                "FL102",
                "Победа",
                "Москва (VKO)",
                "Казань (KZN)",
                "departure",
            ),
            (
                "FL103",
                "Utair",
                "Казань (KZN)",
                "Санкт-Петербург (LED)",
                "arrival",
            ),
            (
                "FL104",
                "Аэрофлот",
                "Санкт-Петербург (LED)",
                "Сочи (AER)",
                "departure",
            ),
            (
                "FL105",
                "S7 Airlines",
                "Москва (DME)",
                "Казань (KZN)",
                "arrival",
            ),
            (
                "FL106",
                "Nordwind",
                "Санкт-Петербург (LED)",
                "Самара (KUF)",
                "arrival",
            ),
        ]

        for index, (
            number,
            airline,
            departure_airport,
            arrival_airport,
            flight_type,
        ) in enumerate(flights_data, start=1):

            departure = now + timedelta(days=index)

            Flight.objects.create(
                flight_number=number,
                airline=airline,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                departure_time=departure,
                arrival_time=departure + timedelta(hours=2),
                flight_type=flight_type,
                gate=f"A{index:02d}",
                seat_capacity=100,
            )

        self.url = reverse("flights:flight_list")

    def test_flights_are_paginated(self):
        first = self.client.get(self.url)
        second = self.client.get(
            self.url,
            {"page": "2"},
        )

        self.assertEqual(first.status_code, 200)
        self.assertContains(first, "Страница 1 из 2")
        self.assertContains(first, "FL101")
        self.assertContains(first, "FL103")
        self.assertNotContains(first, "FL104")

        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "FL104")
        self.assertContains(second, "FL106")
        self.assertNotContains(second, "FL101")

    def test_search_by_flight_number_airline_and_airport(self):
        for query, expected in (
            ("FL103", "FL103"),
            ("Аэрофлот", "FL101"),
            ("Казань", "FL102"),
        ):
            with self.subTest(query=query):
                response = self.client.get(
                    self.url,
                    {"q": query},
                )

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)

    def test_search_and_type_filter_are_combined(self):
        response = self.client.get(
            self.url,
            {
                "q": "Казань",
                "type": "arrival",
            },
        )

        self.assertContains(response, "FL103")
        self.assertContains(response, "FL105")
        self.assertNotContains(response, "FL102")

    def test_descending_order(self):
        response = self.client.get(
            self.url,
            {"sort": "departure_desc"},
        )

        html = response.content.decode("utf-8")

        self.assertEqual(response.status_code, 200)

        self.assertLess(
            html.index("FL106"),
            html.index("FL105"),
        )

        self.assertLess(
            html.index("FL105"),
            html.index("FL104"),
        )

        self.assertNotContains(response, "FL103")

    def test_page_links_preserve_search_and_sort(self):
        response = self.client.get(
            self.url,
            {
                "q": "Санкт-Петербург",
                "sort": "departure_desc",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Страница 1 из 2")
        self.assertContains(response, "sort=departure_desc")
        self.assertContains(response, "page=2")

        second = self.client.get(
            self.url,
            {
                "q": "Санкт-Петербург",
                "sort": "departure_desc",
                "page": "2",
            },
        )

        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "Страница 2 из 2")

    def test_invalid_sort_is_ignored(self):
        response = self.client.get(
            self.url,
            {"sort": "not_a_field"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FL101")


class CheckInListingTests(TestCase):
    """Проверки фильтров и пагинации панели сотрудника."""

    def setUp(self):
        self.staff = User.objects.create_user(
            username="staff_operator",
            password="StrongTestPassword!2026",
            is_staff=True,
        )

        now = timezone.now()
        future_departure = now + timedelta(days=5)
        past_departure = now - timedelta(days=5)

        future = Flight.objects.create(
            flight_number="CHECK100",
            airline="Учебные авиалинии",
            departure_airport="Санкт-Петербург (LED)",
            arrival_airport="Москва (SVO)",
            departure_time=future_departure,
            arrival_time=future_departure + timedelta(hours=2),
            flight_type=Flight.FlightType.DEPARTURE,
            gate="A10",
            seat_capacity=50,
        )

        past = Flight.objects.create(
            flight_number="CHECK200",
            airline="Учебные авиалинии",
            departure_airport="Москва (SVO)",
            arrival_airport="Санкт-Петербург (LED)",
            departure_time=past_departure,
            arrival_time=past_departure + timedelta(hours=2),
            flight_type=Flight.FlightType.ARRIVAL,
            gate="B10",
            seat_capacity=50,
        )

        for index in range(7):
            passenger = User.objects.create_user(
                username=f"passenger_{index}",
                password="StrongTestPassword!2026",
            )

            Reservation.objects.create(
                user=passenger,
                flight=past if index == 6 else future,
                seat_number=index + 1,
            )

        Reservation.objects.filter(
            user__username="passenger_0"
        ).update(
            is_checked_in=True,
            ticket_number="DEMO-TKT-0001",
        )

        self.url = reverse("flights:check_in_list")
        self.client.force_login(self.staff)

    def test_check_in_list_is_paginated(self):
        first = self.client.get(self.url)
        second = self.client.get(
            self.url,
            {"page": "2"},
        )

        self.assertEqual(first.status_code, 200)
        self.assertContains(first, "Страница 1 из 2")
        self.assertContains(first, "Найдено: 7")
        self.assertNotContains(first, "passenger_5")

        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "Страница 2 из 2")
        self.assertContains(second, "passenger_5")

    def test_search_by_passenger(self):
        response = self.client.get(
            self.url,
            {"q": "passenger_5"},
        )

        self.assertContains(response, "passenger_5")
        self.assertNotContains(response, "passenger_4")

    def test_filter_by_registration_status(self):
        registered = self.client.get(
            self.url,
            {"status": "checked_in"},
        )

        self.assertContains(registered, "passenger_0")
        self.assertNotContains(registered, "passenger_1")

        pending = self.client.get(
            self.url,
            {"status": "pending"},
        )

        self.assertContains(pending, "passenger_1")
        self.assertNotContains(pending, "passenger_0")
        self.assertNotContains(pending, "passenger_6")

        closed = self.client.get(
            self.url,
            {"status": "closed"},
        )

        self.assertContains(closed, "passenger_6")
        self.assertNotContains(closed, "passenger_1")

    def test_search_parameters_are_preserved_in_page_links(self):
        response = self.client.get(
            self.url,
            {
                "q": "passenger_",
                "sort": "passenger",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "q=passenger_")
        self.assertContains(response, "sort=passenger")
        self.assertContains(response, "page=2")

    def test_invalid_status_and_sort_are_ignored(self):
        response = self.client.get(
            self.url,
            {
                "status": "unknown",
                "sort": "bad_field",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Найдено: 7")