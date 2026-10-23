from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CarForm, CarOwnerForm
from .models import Car, CarOwner, DriverLicense


# Function-Based Views

def owner_list(request):
    """Список владельцев с количеством автомобилей."""

    owners = CarOwner.objects.annotate(
        car_count=Count("cars", distinct=True)
    )

    return render(
        request,
        "project_first_app/owner_list.html",
        {"owners": owners},
    )


def owner_detail(request, owner_id):
    """Подробная информация о владельце автомобиля."""

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


@staff_member_required
def owner_create(request):
    """Создание владельца с помощью FBV и ModelForm."""

    if request.method == "POST":
        form = CarOwnerForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("project_first_app:owner_list")

    else:
        form = CarOwnerForm()

    return render(
        request,
        "project_first_app/owner_form.html",
        {"form": form},
    )


# Class-Based Views

class CarListView(ListView):
    """Список всех автомобилей."""

    model = Car
    template_name = "project_first_app/car_list.html"
    context_object_name = "cars"


class CarDetailView(DetailView):
    """Подробная информация об автомобиле."""

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


class CarCreateView(CreateView):
    """Создание нового автомобиля."""

    model = Car
    form_class = CarForm
    template_name = "project_first_app/car_form.html"

    success_url = reverse_lazy(
        "project_first_app:car_list"
    )


class CarUpdateView(UpdateView):
    """Редактирование существующего автомобиля."""

    model = Car
    form_class = CarForm
    template_name = "project_first_app/car_form.html"

    success_url = reverse_lazy(
        "project_first_app:car_list"
    )


class CarDeleteView(DeleteView):
    """Удаление автомобиля с подтверждением."""

    model = Car

    template_name = (
        "project_first_app/car_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "project_first_app:car_list"
    )