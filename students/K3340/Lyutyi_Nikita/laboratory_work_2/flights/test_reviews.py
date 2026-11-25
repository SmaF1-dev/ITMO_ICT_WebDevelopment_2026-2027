from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Flight, Review


User = get_user_model()


class ReviewTests(TestCase):
    """Проверки отзывов об авиарейсах."""

    def setUp(self):
        now = timezone.now()

        past_departure = now - timedelta(days=3)
        future_departure = now + timedelta(days=3)

        self.flight = Flight.objects.create(
            flight_number="TEST100",
            airline="Учебные авиалинии",
            departure_airport="Санкт-Петербург (LED)",
            arrival_airport="Москва (SVO)",
            departure_time=past_departure,
            arrival_time=past_departure + timedelta(hours=2),
            flight_type=Flight.FlightType.DEPARTURE,
            gate="A01",
            seat_capacity=50,
        )

        self.future_flight = Flight.objects.create(
            flight_number="TEST200",
            airline="Учебные авиалинии",
            departure_airport="Москва (SVO)",
            arrival_airport="Санкт-Петербург (LED)",
            departure_time=future_departure,
            arrival_time=future_departure + timedelta(hours=2),
            flight_type=Flight.FlightType.ARRIVAL,
            gate="B01",
            seat_capacity=50,
        )

        self.user = User.objects.create_user(
            username="review_author",
            password="StrongTestPassword!2026",
        )

        self.other_user = User.objects.create_user(
            username="another_author",
            password="AnotherStrongPassword!2026",
        )

    def create_review(
        self,
        author=None,
        rating=8,
        text="Хороший учебный рейс.",
    ):
        """Создаёт отзыв в тестовой базе."""

        return Review.objects.create(
            flight=self.flight,
            author=author or self.user,
            flight_date=timezone.localtime(
                self.flight.departure_time
            ).date(),
            text=text,
            rating=rating,
        )

    def test_review_requires_login(self):
        """Гость должен сначала авторизоваться."""

        url = reverse(
            "flights:review_create",
            kwargs={"pk": self.flight.pk},
        )

        response = self.client.get(url)

        self.assertRedirects(
            response,
            reverse("accounts:login") + "?next=" + url,
        )

    def test_review_cannot_be_created_before_arrival(self):
        """Нельзя оценивать ещё не завершённый рейс."""

        self.client.force_login(self.user)

        url = reverse(
            "flights:review_create",
            kwargs={"pk": self.future_flight.pk},
        )

        get_response = self.client.get(url)

        post_response = self.client.post(
            url,
            {
                "rating": "8",
                "text": "Тестовый отзыв.",
            },
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(Review.objects.count(), 0)

    def test_review_creation_sets_server_fields(self):
        """Автор, рейс и дата определяются сервером."""

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:review_create",
                kwargs={"pk": self.flight.pk},
            ),
            {
                "rating": "8",
                "text": "Хороший рейс и вежливый персонал.",
                "author": self.other_user.pk,
                "flight": self.future_flight.pk,
                "flight_date": "2000-01-01",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            ),
        )

        review = Review.objects.get()

        self.assertEqual(review.author, self.user)
        self.assertEqual(review.flight, self.flight)
        self.assertEqual(review.rating, 8)
        self.assertEqual(
            review.flight_date,
            timezone.localtime(
                self.flight.departure_time
            ).date(),
        )

    def test_rating_out_of_range_is_rejected(self):
        """Оценка должна находиться в диапазоне 1–10."""

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:review_create",
                kwargs={"pk": self.flight.pk},
            ),
            {
                "rating": "11",
                "text": "Текст отзыва.",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Review.objects.filter(
                flight=self.flight,
                author=self.user,
            ).exists()
        )

    def test_existing_review_redirects_to_edit(self):
        """Повторная публикация не создаёт второй отзыв."""

        review = self.create_review()

        self.client.force_login(self.user)

        response = self.client.get(
            reverse(
                "flights:review_create",
                kwargs={"pk": self.flight.pk},
            )
        )

        self.assertRedirects(
            response,
            reverse(
                "flights:review_update",
                kwargs={"pk": review.pk},
            ),
        )

        self.assertEqual(Review.objects.count(), 1)

    def test_user_can_edit_own_review(self):
        """Автор может изменить свою оценку и текст."""

        review = self.create_review()

        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "flights:review_update",
                kwargs={"pk": review.pk},
            ),
            {
                "rating": "9",
                "text": "Обновлённая оценка полёта.",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            ),
        )

        review.refresh_from_db()

        self.assertEqual(review.rating, 9)
        self.assertEqual(
            review.text,
            "Обновлённая оценка полёта.",
        )
        self.assertEqual(review.author, self.user)

    def test_user_can_delete_own_review(self):
        """Удаление выполняется через POST."""

        review = self.create_review()

        self.client.force_login(self.user)

        url = reverse(
            "flights:review_delete",
            kwargs={"pk": review.pk},
        )

        get_response = self.client.get(url)

        self.assertEqual(get_response.status_code, 200)

        self.assertTrue(
            Review.objects.filter(pk=review.pk).exists()
        )

        post_response = self.client.post(url)

        self.assertRedirects(
            post_response,
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            ),
        )

        self.assertFalse(
            Review.objects.filter(pk=review.pk).exists()
        )

    def test_user_cannot_change_another_review(self):
        """Чужой отзыв нельзя изменить или удалить."""

        review = self.create_review(
            author=self.other_user,
        )

        self.client.force_login(self.user)

        update_url = reverse(
            "flights:review_update",
            kwargs={"pk": review.pk},
        )

        delete_url = reverse(
            "flights:review_delete",
            kwargs={"pk": review.pk},
        )

        self.assertEqual(
            self.client.get(update_url).status_code,
            404,
        )

        self.assertEqual(
            self.client.post(
                update_url,
                {
                    "rating": "1",
                    "text": "Попытка изменения.",
                },
            ).status_code,
            404,
        )

        self.assertEqual(
            self.client.get(delete_url).status_code,
            404,
        )

        self.assertEqual(
            self.client.post(delete_url).status_code,
            404,
        )

        review.refresh_from_db()

        self.assertEqual(review.rating, 8)
        self.assertEqual(
            review.text,
            "Хороший учебный рейс.",
        )

    def test_flight_detail_shows_review_average(self):
        """Страница рейса показывает отзывы и среднюю оценку."""

        self.create_review(
            author=self.user,
            rating=8,
            text="Первый отзыв.",
        )

        self.create_review(
            author=self.other_user,
            rating=10,
            text="Второй отзыв.",
        )

        response = self.client.get(
            reverse(
                "flights:flight_detail",
                kwargs={"pk": self.flight.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Первый отзыв.")
        self.assertContains(response, "Второй отзыв.")
        self.assertContains(response, "9.0 / 10")
        self.assertContains(response, "Отзывов: 2")

    def test_database_rejects_duplicate_review(self):
        """PostgreSQL запрещает два отзыва автора на один рейс."""

        self.create_review(
            author=self.user,
            rating=8,
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_review(
                    author=self.user,
                    rating=9,
                    text="Повторный отзыв.",
                )

        self.assertEqual(
            Review.objects.count(),
            1,
        )