from django.contrib import admin

from .models import Car, CarOwner, DriverLicense, Ownership


@admin.register(CarOwner)
class CarOwnerAdmin(admin.ModelAdmin):
    """Административный интерфейс владельцев."""

    list_display = (
        "id",
        "first_name",
        "last_name",
        "birth_date",
    )

    search_fields = (
        "first_name",
        "last_name",
    )

    ordering = ("last_name", "first_name")

    list_per_page = 20


@admin.register(DriverLicense)
class DriverLicenseAdmin(admin.ModelAdmin):
    """Административный интерфейс водительских удостоверений."""

    list_display = (
        "number",
        "owner",
        "issue_date",
        "expiry_date",
    )

    search_fields = (
        "number",
        "owner__first_name",
        "owner__last_name",
    )

    list_select_related = ("owner",)


class OwnershipInline(admin.TabularInline):
    """История владения непосредственно на странице автомобиля."""

    model = Ownership

    extra = 0

    autocomplete_fields = ("owner",)

    fields = (
        "owner",
        "start_date",
        "end_date",
    )


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    """Административный интерфейс автомобилей."""

    list_display = (
        "id",
        "brand",
        "model",
        "registration_number",
        "color",
    )

    search_fields = (
        "brand",
        "model",
        "registration_number",
    )

    list_filter = ("color",)

    inlines = (OwnershipInline,)

    list_per_page = 20


@admin.register(Ownership)
class OwnershipAdmin(admin.ModelAdmin):
    """Административный интерфейс истории владения."""

    list_display = (
        "car",
        "owner",
        "start_date",
        "end_date",
    )

    search_fields = (
        "car__brand",
        "car__model",
        "car__registration_number",
        "owner__first_name",
        "owner__last_name",
    )

    list_filter = ("start_date", "end_date")

    autocomplete_fields = ("car", "owner")

    list_select_related = ("car", "owner")

    list_per_page = 20