from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AuthenticationTests(TestCase):
    """Проверки регистрации и авторизации пользователей."""

    def setUp(self):
        self.password = "StrongTestPassword!2026"

    def test_registration_creates_regular_user(self):
        """Регистрация создаёт пользователя без прав администратора."""

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "flight_test",
                "first_name": "Андрей",
                "last_name": "Лебедев",
                "email": "flight_test@example.com",
                "password1": self.password,
                "password2": self.password,
            },
        )

        self.assertRedirects(
            response,
            reverse("project_first_app:car_list"),
        )

        user = User.objects.get(
            username="flight_test"
        )

        self.assertTrue(
            user.check_password(self.password)
        )

        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        self.assertEqual(
            self.client.session["_auth_user_id"],
            str(user.pk),
        )

    def test_registration_rejects_different_passwords(self):
        """Пароли должны совпадать."""

        response = self.client.post(
            reverse("accounts:register"),
            {
                "username": "invalid_user",
                "first_name": "Тест",
                "last_name": "Пользователь",
                "email": "invalid@example.com",
                "password1": self.password,
                "password2": "DifferentPassword!2026",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            User.objects.filter(
                username="invalid_user"
            ).exists()
        )

        self.assertIn(
            "password2",
            response.context["form"].errors,
        )

    def test_login_and_logout(self):
        """Пользователь может войти и завершить сессию."""

        user = User.objects.create_user(
            username="existing_user",
            password=self.password,
        )

        login_response = self.client.post(
            reverse("accounts:login"),
            {
                "username": user.username,
                "password": self.password,
            },
        )

        self.assertRedirects(
            login_response,
            reverse("project_first_app:car_list"),
        )

        self.assertEqual(
            self.client.session["_auth_user_id"],
            str(user.pk),
        )

        logout_response = self.client.post(
            reverse("accounts:logout"),
        )

        self.assertRedirects(
            logout_response,
            reverse("accounts:login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )

    def test_logout_requires_post(self):
        """Выход не должен выполняться через GET."""

        response = self.client.get(
            reverse("accounts:logout")
        )

        self.assertEqual(response.status_code, 405)