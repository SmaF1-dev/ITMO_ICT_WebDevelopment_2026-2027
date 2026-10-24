from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
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

from .forms import (
    CarForm,
    CarOwnerForm,
    OwnerUserCreationForm,
)
from .models import Car, CarOwner, DriverLicense


# Function-Based Views

def owner_list(request):
    """Список владельцев и связанных учётных записей."""

    owners = (
        CarOwner.objects
        .select_related("user")
        .annotate(
            car_count=Count("cars", distinct=True)
        )
    )

    return render(
        request,
        "project_first_app/owner_list.html",
        {"owners": owners},
    )


def owner_detail(request, owner_id):
    """Информация о владельце и его учётной записи."""

    owner = get_object_or_404(
        CarOwner.objects.select_related("user"),
        pk=owner_id,
    )

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
    """Создание владельца через ModelForm из практики 2.2."""

    if request.method == "POST":
        form = CarOwnerForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect(
                "project_first_app:owner_list"
            )
    else:
        form = CarOwnerForm()

    return render(
        request,
        "project_first_app/owner_form.html",
        {"form": form},
    )


@staff_member_required
def owner_user_create(request):
    """Создание пользователя и связанного владельца."""

    if request.method == "POST":
        form = OwnerUserCreationForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                user = form.save()

                owner = CarOwner.objects.create(
                    user=user,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    birth_date=form.cleaned_data["birth_date"],
                )

            return redirect(
                "project_first_app:owner_detail",
                owner_id=owner.pk,
            )
    else:
        form = OwnerUserCreationForm()

    return render(
        request,
        "project_first_app/owner_user_form.html",
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
    """Создание автомобиля."""

    model = Car
    form_class = CarForm
    template_name = "project_first_app/car_form.html"

    success_url = reverse_lazy(
        "project_first_app:car_list"
    )


class CarUpdateView(UpdateView):
    """Редактирование автомобиля."""

    model = Car
    form_class = CarForm
    template_name = "project_first_app/car_form.html"

    success_url = reverse_lazy(
        "project_first_app:car_list"
    )


class CarDeleteView(DeleteView):
    """Удаление автомобиля."""

    model = Car

    template_name = (
        "project_first_app/car_confirm_delete.html"
    )

    success_url = reverse_lazy(
        "project_first_app:car_list"
    )