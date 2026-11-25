from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class CarOwner(models.Model):
    """Владелец автомобиля."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="car_owner_profile",
        verbose_name="Учётная запись",
    )

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Владелец автомобиля"
        verbose_name_plural = "Владельцы автомобилей"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DriverLicense(models.Model):
    """Водительское удостоверение владельца."""

    owner = models.OneToOneField(
        CarOwner,
        on_delete=models.CASCADE,
        related_name="driver_license",
    )

    number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()

    class Meta:
        verbose_name = "Водительское удостоверение"
        verbose_name_plural = "Водительские удостоверения"

    def clean(self):
        super().clean()

        if self.issue_date and self.expiry_date:
            if self.expiry_date <= self.issue_date:
                raise ValidationError({
                    "expiry_date": (
                        "Срок окончания должен быть позже даты выдачи."
                    )
                })

    def __str__(self):
        return self.number


class Car(models.Model):
    """Автомобиль."""

    class Color(models.TextChoices):
        BLACK = "black", "Чёрный"
        WHITE = "white", "Белый"
        GRAY = "gray", "Серый"
        RED = "red", "Красный"
        BLUE = "blue", "Синий"

    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)

    color = models.CharField(
        max_length=10,
        choices=Color.choices,
    )

    registration_number = models.CharField(
        max_length=20,
        unique=True,
    )

    owners = models.ManyToManyField(
        CarOwner,
        through="Ownership",
        related_name="cars",
    )

    class Meta:
        ordering = ["brand", "model"]
        verbose_name = "Автомобиль"
        verbose_name_plural = "Автомобили"

    def __str__(self):
        return f"{self.brand} {self.model} ({self.registration_number})"


class Ownership(models.Model):
    """История владения автомобилем."""

    owner = models.ForeignKey(
        CarOwner,
        on_delete=models.CASCADE,
        related_name="ownerships",
    )

    car = models.ForeignKey(
        Car,
        on_delete=models.CASCADE,
        related_name="ownerships",
    )

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "История владения"
        verbose_name_plural = "История владения"

    def clean(self):
        super().clean()

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({
                    "end_date": (
                        "Дата окончания не может быть раньше даты начала."
                    )
                })

        if not self.car_id or not self.start_date:
            return

        overlapping = Ownership.objects.filter(
            car_id=self.car_id,
        ).exclude(
            pk=self.pk,
        ).filter(
            Q(end_date__isnull=True)
            | Q(end_date__gte=self.start_date)
        )

        if self.end_date is not None:
            overlapping = overlapping.filter(
                start_date__lte=self.end_date,
            )

        if overlapping.exists():
            raise ValidationError(
                "Период владения пересекается с другой записью "
                "для этого автомобиля."
            )

    def __str__(self):
        return f"{self.owner} — {self.car}"