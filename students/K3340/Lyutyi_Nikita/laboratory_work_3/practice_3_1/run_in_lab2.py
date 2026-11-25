"""Практика 3.1: запускать из корня ЛР2 командой python <путь к этому файлу>."""

import os
import sys
from datetime import date
from pathlib import Path

STANDALONE = os.getenv("PRACTICE_3_1_STANDALONE") == "1"
if STANDALONE:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    os.environ["DJANGO_SETTINGS_MODULE"] = "practice_3_1_settings"
else:
    sys.path.insert(0, str(Path.cwd()))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_project_lyutyi.settings")

import django

django.setup()

from django.db import transaction
from django.db.models import Count, Max, Min
if STANDALONE:
    from cars_practice.models import Car, CarOwner, DriverLicense, Ownership
else:
    from project_first_app.models import Car, CarOwner, DriverLicense, Ownership


@transaction.atomic
def seed():
    persons = [
        ("Олег", "Практиков"),
        ("Анна", "Михеева"),
        ("Иван", "Семенов"),
        ("Мария", "Орлова"),
        ("Дмитрий", "Васильев"),
        ("Елена", "Ковалева"),
    ]
    owners = []
    for i, (first, last) in enumerate(persons):
        owner, _ = CarOwner.objects.get_or_create(
            first_name=first, last_name=last,
            defaults={"birth_date": date(1990, 1, 10 + i)},
        )
        DriverLicense.objects.get_or_create(
            owner=owner,
            defaults={"number": f"LR3-2026-{i + 1:03d}",
                      "issue_date": date(2014, 1, 10 + i),
                      "expiry_date": date(2028, 1, 10 + i)},
        )
        owners.append(owner)

    brands = ["Toyota", "Volkswagen", "Toyota", "Honda", "Lada", "BMW"]
    cars = []
    for i, brand in enumerate(brands):
        car, _ = Car.objects.get_or_create(
            registration_number=f"LR3-AUTO-{i + 1:02d}",
            defaults={"brand": brand, "model": f"Demo-{i + 1}",
                      "color": "red" if i % 2 == 0 else "blue"},
        )
        cars.append(car)

    for i, car in enumerate(cars):
        Ownership.objects.get_or_create(
            car=car, owner=owners[(i - 1) % 6], start_date=date(2010, 1, 1),
            defaults={"end_date": date(2012, 12, 31)},
        )
        Ownership.objects.get_or_create(
            car=car, owner=owners[i], start_date=date(2013, 1, 1),
            defaults={"end_date": None},
        )
    return owners


def run_queries(owners):
    print("1. Автомобили марки Toyota:", list(Car.objects.filter(brand="Toyota")))
    print("2. Владельцы по имени Олег:", list(CarOwner.objects.filter(first_name="Олег")))
    print("3. Удостоверение по ID владельца:", DriverLicense.objects.get(owner_id=owners[0].pk))
    print("4. Владельцы красных автомобилей:", list(
        CarOwner.objects.filter(ownerships__car__color="red").distinct()
    ))
    print("5. Владельцы, у которых есть период владения с 2010 года:", list(
        CarOwner.objects.filter(ownerships__start_date__year=2010).distinct()
    ))
    print("6. Самая ранняя дата выдачи прав:", DriverLicense.objects.aggregate(earliest=Min("issue_date")))
    print("7. Последняя дата начала владения автомобилем Demo-1:", Ownership.objects.filter(
        car__model="Demo-1").aggregate(latest=Max("start_date")))
    print("8. Количество разных автомобилей у каждого владельца:", list(
        CarOwner.objects.annotate(cars_count=Count("cars", distinct=True))
        .values("first_name", "last_name", "cars_count")
    ))
    print("9. Количество автомобилей каждой марки:", list(
        Car.objects.values("brand").annotate(total=Count("id")).order_by("brand")
    ))
    print("10. Владельцы по дате выдачи удостоверения:", list(
        CarOwner.objects.filter(driver_license__isnull=False)
        .order_by("driver_license__issue_date").distinct()
    ))


if __name__ == "__main__":
    data = seed()
    run_queries(data)
