from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView

from .models import Car, CarOwner, DriverLicense


# Function-Based Views

def owner_list(request):
    """Список владельцев и количество их автомобилей."""

    owners = CarOwner.objects.annotate(
        car_count=Count("cars", distinct=True)
    )

    return render(
        request,
        "project_first_app/owner_list.html",
        {"owners": owners},
    )


def owner_detail(request, owner_id):
    """Информация о владельце автомобиля."""

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


# Class-Based Views

class CarListView(ListView):
    """Список всех автомобилей."""

    model = Car
    template_name = "project_first_app/car_list.html"
    context_object_name = "cars"


class CarDetailView(DetailView):
    """Информация о конкретном автомобиле."""

    model = Car
    template_name = "project_first_app/car_detail.html"
    context_object_name = "car"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["ownerships"] = (
            self.object.ownerships
            .select_related("owner")
            .all()
        )

        return context


class CarUpdateView(UpdateView):
    """Редактирование автомобиля."""

    model = Car

    fields = [
        "brand",
        "model",
        "color",
        "registration_number",
    ]

    template_name = "project_first_app/car_form.html"

    success_url = reverse_lazy("project_first_app:car_list")