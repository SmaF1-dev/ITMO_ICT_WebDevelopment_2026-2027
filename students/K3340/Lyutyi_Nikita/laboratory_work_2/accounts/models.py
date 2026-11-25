from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь с дополнительными персональными данными."""

    passport_number = models.CharField(
        "Номер паспорта",
        max_length=20,
        unique=True,
        null=True,
        blank=True,
    )

    home_address = models.CharField(
        "Домашний адрес",
        max_length=255,
        blank=True,
    )

    nationality = models.CharField(
        "Национальность",
        max_length=80,
        blank=True,
    )

    def __str__(self):
        return self.username