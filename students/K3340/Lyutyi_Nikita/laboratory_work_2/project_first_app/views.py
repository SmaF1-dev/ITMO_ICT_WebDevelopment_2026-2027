from django.shortcuts import get_object_or_404, render

from .models import CarOwner, DriverLicense


def owner_detail(request, owner_id):
    """Отображает данные владельца автомобиля по его ID."""

    owner = get_object_or_404(CarOwner, pk=owner_id)

    ownerships = owner.ownerships.select_related("car").all()

    driver_license = DriverLicense.objects.filter(
        owner=owner,
    ).first()

    context = {
        "owner": owner,
        "ownerships": ownerships,
        "driver_license": driver_license,
    }

    return render(
        request,
        "project_first_app/owner_detail.html",
        context,
    )