"""Учебная копия структуры автомобильных моделей ЛР2 для независимого запуска практики."""
from django.db import models


class CarOwner(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birth_date = models.DateField(null=True, blank=True)
    class Meta:
        ordering = ["last_name", "first_name"]
    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class DriverLicense(models.Model):
    owner = models.OneToOneField(CarOwner, on_delete=models.CASCADE, related_name="driver_license")
    number = models.CharField(max_length=20, unique=True)
    issue_date = models.DateField()
    expiry_date = models.DateField()
    def __str__(self):
        return self.number


class Car(models.Model):
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    color = models.CharField(max_length=10)
    registration_number = models.CharField(max_length=20, unique=True)
    owners = models.ManyToManyField(CarOwner, through="Ownership", related_name="cars")
    def __str__(self):
        return f"{self.brand} {self.model}"


class Ownership(models.Model):
    owner = models.ForeignKey(CarOwner, on_delete=models.CASCADE, related_name="ownerships")
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="ownerships")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
