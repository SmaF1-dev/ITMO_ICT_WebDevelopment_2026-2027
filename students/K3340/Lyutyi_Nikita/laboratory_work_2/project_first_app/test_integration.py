
from datetime import date

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from .models import Car, CarOwner, DriverLicense, Ownership


User = get_user_model()


class PracticeModelTests(TestCase):
    """Связи, уникальность и валидация практики 2.1."""

    @classmethod
    def setUpTestData(cls):
        cls.ivan = CarOwner.objects.create(
            first_name="Иван",
            last_name="Петров",
            birth_date=date(1990, 4, 15),
        )

        cls.maria = CarOwner.objects.create(
            first_name="Мария",
            last_name="Соколова",
            birth_date=date(1995, 8, 20),
        )

        cls.bmw = Car.objects.create(
            brand="BMW",
            model="320i",
            color=Car.Color.BLACK,
            registration_number="A111AA",
        )

        cls.kia = Car.objects.create(
            brand="Kia",
            model="Rio",
            color=Car.Color.WHITE,
            registration_number="B222BB",
        )

        Ownership.objects.create(
            owner=cls.ivan,
            car=cls.bmw,
            start_date=date(2020, 1, 1),
            end_date=date(2021, 12, 31),
        )

        Ownership.objects.create(
            owner=cls.maria,
            car=cls.bmw,
            start_date=date(2022, 1, 1),
        )

        Ownership.objects.create(
            owner=cls.ivan,
            car=cls.kia,
            start_date=date(2023, 1, 1),
        )

    def test_str_representation(self):
        self.assertEqual(str(self.ivan), "Иван Петров")
        self.assertEqual(str(self.bmw), "BMW 320i (A111AA)")

    def test_many_to_many_uses_ownership_history(self):
        self.assertEqual(
            set(self.bmw.owners.values_list("pk", flat=True)),
            {self.ivan.pk, self.maria.pk},
        )

        self.assertEqual(self.ivan.cars.count(), 2)

        self.assertEqual(
            Ownership.objects.filter(car=self.bmw).count(),
            2,
        )

    def test_non_overlapping_period_is_allowed(self):
        record = Ownership(
            owner=self.maria,
            car=self.kia,
            start_date=date(2018, 1, 1),
            end_date=date(2019, 12, 31),
        )

        record.full_clean()
        record.save()

        self.assertTrue(
            Ownership.objects.filter(pk=record.pk).exists()
        )

    def test_overlapping_period_is_rejected(self):
        record = Ownership(
            owner=self.ivan,
            car=self.bmw,
            start_date=date(2023, 6, 1),
            end_date=date(2023, 12, 31),
        )

        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_end_date_before_start_date_is_rejected(self):
        record = Ownership(
            owner=self.maria,
            car=self.kia,
            start_date=date(2019, 12, 31),
            end_date=date(2019, 1, 1),
        )

        with self.assertRaises(ValidationError):
            record.full_clean()

    def test_driver_license_one_to_one_relation(self):
        license_record = DriverLicense.objects.create(
            owner=self.ivan,
            number="77 11 123456",
            issue_date=date(2020, 1, 1),
            expiry_date=date(2030, 1, 1),
        )

        self.assertEqual(
            self.ivan.driver_license,
            license_record,
        )

    def test_driver_license_expiry_is_validated(self):
        license_record = DriverLicense(
            owner=self.ivan,
            number="77 11 123456",
            issue_date=date(2025, 1, 1),
            expiry_date=date(2024, 12, 31),
        )

        with self.assertRaises(ValidationError):
            license_record.full_clean()

    def test_registration_number_must_be_unique(self):
        duplicate = Car(
            brand="Другой бренд",
            model="Другая модель",
            color=Car.Color.RED,
            registration_number=self.bmw.registration_number,
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_models_are_registered_in_admin(self):
        for model in (
            Car,
            CarOwner,
            DriverLicense,
            Ownership,
        ):
            with self.subTest(model=model.__name__):
                self.assertIn(model, admin.site._registry)


class PracticeViewTests(TestCase):
    """FBV, CBV, формы и права доступа практик 2.1–2.2."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser(
            username="lab_admin",
            email="lab_admin@example.com",
            password="StrongTestPassword!2026",
        )

        cls.visitor = User.objects.create_user(
            username="lab_visitor",
            password="StrongTestPassword!2026",
        )

        cls.owner = CarOwner.objects.create(
            first_name="Алексей",
            last_name="Смирнов",
            birth_date=date(1988, 3, 12),
        )

        cls.car = Car.objects.create(
            brand="Toyota",
            model="Corolla",
            color=Car.Color.GRAY,
            registration_number="C333CC",
        )

        Ownership.objects.create(
            owner=cls.owner,
            car=cls.car,
            start_date=date(2020, 1, 1),
        )

    def test_public_lists_are_available(self):
        for url, expected_text in (
            (
                reverse("project_first_app:owner_list"),
                "Смирнов",
            ),
            (
                reverse("project_first_app:car_list"),
                "Corolla",
            ),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected_text)

    def test_owner_detail_shows_ownership(self):
        response = self.client.get(
            reverse(
                "project_first_app:owner_detail",
                kwargs={"owner_id": self.owner.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Алексей")
        self.assertContains(response, "Toyota")
        self.assertContains(response, "Corolla")

    def test_car_detail_shows_history(self):
        response = self.client.get(
            reverse(
                "project_first_app:car_detail",
                kwargs={"pk": self.car.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Corolla")
        self.assertContains(response, "Смирнов")

    def test_nonexistent_objects_return_404(self):
        for url in (
            reverse(
                "project_first_app:owner_detail",
                kwargs={"owner_id": 999999},
            ),
            reverse(
                "project_first_app:car_detail",
                kwargs={"pk": 999999},
            ),
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_open_edit_forms(self):
        urls = (
            "/owners/new/",
            "/cars/new/",
            f"/cars/{self.car.pk}/edit/",
            f"/cars/{self.car.pk}/delete/",
            "/owners/users/new/",
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)

    def test_regular_user_cannot_open_staff_forms(self):
        self.client.force_login(self.visitor)

        for url in (
            "/owners/new/",
            "/cars/new/",
            f"/cars/{self.car.pk}/edit/",
            f"/cars/{self.car.pk}/delete/",
            "/owners/users/new/",
        ):
            with self.subTest(url=url):
                response = self.client.get(url)

                self.assertNotEqual(
                    response.status_code,
                    200,
                )

    def test_staff_can_create_owner(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            "/owners/new/",
            {
                "first_name": "Ольга",
                "last_name": "Кузнецова",
                "birth_date": "1992-06-17",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            CarOwner.objects.filter(
                first_name="Ольга",
                last_name="Кузнецова",
            ).exists()
        )

    def test_staff_can_create_car(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            "/cars/new/",
            {
                "brand": "Ford",
                "model": "Focus",
                "color": Car.Color.BLUE,
                "registration_number": "D444DD",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            Car.objects.filter(
                registration_number="D444DD"
            ).exists()
        )

    def test_duplicate_car_number_is_rejected_by_form(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            "/cars/new/",
            {
                "brand": "Ford",
                "model": "Focus",
                "color": Car.Color.BLUE,
                "registration_number": (
                    self.car.registration_number
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Car.objects.count(), 1)

    def test_staff_can_update_car(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            f"/cars/{self.car.pk}/edit/",
            {
                "brand": "Toyota",
                "model": "Camry",
                "color": Car.Color.BLACK,
                "registration_number": "C333CC",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.car.refresh_from_db()

        self.assertEqual(self.car.model, "Camry")
        self.assertEqual(self.car.color, Car.Color.BLACK)

    def test_get_delete_page_does_not_remove_car(self):
        self.client.force_login(self.staff)

        response = self.client.get(
            f"/cars/{self.car.pk}/delete/"
        )

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            Car.objects.filter(pk=self.car.pk).exists()
        )

    def test_staff_can_delete_car_and_its_history(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            f"/cars/{self.car.pk}/delete/"
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Car.objects.filter(pk=self.car.pk).exists()
        )

        self.assertFalse(
            Ownership.objects.filter(
                car_id=self.car.pk
            ).exists()
        )

        self.assertTrue(
            CarOwner.objects.filter(
                pk=self.owner.pk
            ).exists()
        )


class OwnerUserTests(TestCase):
    """Расширенная модель пользователя и практика 2.3."""

    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser(
            username="owner_admin",
            email="owner_admin@example.com",
            password="StrongTestPassword!2026",
        )

    def test_extended_user_fields_and_profile_relation(self):
        user = User.objects.create_user(
            username="model_owner",
            password="StrongTestPassword!2026",
            first_name="Елена",
            last_name="Морозова",
            passport_number="DEMO-9001",
            home_address="Учебный адрес, дом 1",
            nationality="Тестовая",
        )

        profile = CarOwner.objects.create(
            user=user,
            first_name="Елена",
            last_name="Морозова",
        )

        self.assertEqual(
            user.passport_number,
            "DEMO-9001",
        )

        self.assertEqual(
            user.home_address,
            "Учебный адрес, дом 1",
        )

        self.assertEqual(
            user.nationality,
            "Тестовая",
        )

        self.assertEqual(
            user.car_owner_profile,
            profile,
        )

        self.assertTrue(
            user.check_password("StrongTestPassword!2026")
        )

    def test_staff_can_create_user_and_owner_together(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            "/owners/users/new/",
            {
                "username": "created_owner",
                "first_name": "Сергей",
                "last_name": "Иванов",
                "email": "created_owner@example.com",
                "birth_date": "1998-05-10",
                "passport_number": "DEMO-9002",
                "home_address": "Учебный адрес, дом 2",
                "nationality": "Тестовая",
                "password1": "StrongTestPassword!2026",
                "password2": "StrongTestPassword!2026",
            },
        )

        self.assertEqual(response.status_code, 302)

        user = User.objects.get(
            username="created_owner"
        )

        self.assertEqual(
            user.car_owner_profile.first_name,
            "Сергей",
        )

        self.assertEqual(
            user.car_owner_profile.last_name,
            "Иванов",
        )

        self.assertTrue(
            user.check_password("StrongTestPassword!2026")
        )

    def test_password_mismatch_does_not_create_user(self):
        self.client.force_login(self.staff)

        response = self.client.post(
            "/owners/users/new/",
            {
                "username": "invalid_owner",
                "first_name": "Сергей",
                "last_name": "Иванов",
                "email": "invalid_owner@example.com",
                "birth_date": "1998-05-10",
                "passport_number": "DEMO-9003",
                "home_address": "Учебный адрес, дом 3",
                "nationality": "Тестовая",
                "password1": "StrongTestPassword!2026",
                "password2": "DifferentPassword!2026",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            User.objects.filter(
                username="invalid_owner"
            ).exists()
        )

        self.assertEqual(
            CarOwner.objects.count(),
            0,
        )
