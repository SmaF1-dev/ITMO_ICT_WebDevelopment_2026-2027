from django.http import JsonResponse
from django.urls import path

from cars_practice.models import Car, CarOwner, DriverLicense, Ownership


def practice_status(request):
    """Небольшая веб-проверка автономной базы ORM-практики."""
    return JsonResponse({
        "practice": "3.1",
        "status": "ok",
        "description": "Django ORM: автомобили и владельцы",
        "owners": CarOwner.objects.count(),
        "cars": Car.objects.count(),
        "licenses": DriverLicense.objects.count(),
        "ownership_periods": Ownership.objects.count(),
    })


urlpatterns = [path("", practice_status, name="practice-3-1-status")]
