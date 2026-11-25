from django.contrib import admin


class ReadOnlyAgencyAdmin(admin.ModelAdmin):
    """Данные о заказах меняются только через API, где работают блокировки."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
from .models import (
    Advertiser, AdvertisingRequest, AdvertisingService, Contract,
    Employee, Material, MaterialUsageNorm, PaymentOrder, RequestWork, ServiceCategory,
)


@admin.register(Advertiser)
class AdvertiserAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "phone", "email")
    search_fields = ("last_name", "first_name")


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(AdvertisingService)
class AdvertisingServiceAdmin(ReadOnlyAgencyAdmin):
    list_display = ("name", "category", "unit", "current_price")
    list_filter = ("category",)
    search_fields = ("name",)


@admin.register(Material)
class MaterialAdmin(ReadOnlyAgencyAdmin):
    list_display = ("name", "unit")
    search_fields = ("name",)


@admin.register(AdvertisingRequest)
class AdvertisingRequestAdmin(ReadOnlyAgencyAdmin):
    list_display = ("request_id", "advertiser", "contact_person", "submitted_at")
    search_fields = ("advertiser__name", "contact_person")


@admin.register(RequestWork)
class RequestWorkAdmin(ReadOnlyAgencyAdmin):
    list_display = ("request", "service", "employee", "quantity", "agreed_unit_price")


@admin.register(Contract)
class ContractAdmin(ReadOnlyAgencyAdmin):
    list_display = ("contract_number", "request", "signed_at")


@admin.register(PaymentOrder)
class PaymentOrderAdmin(ReadOnlyAgencyAdmin):
    list_display = ("document_number", "contract", "issued_at", "amount_due", "paid_at")
    readonly_fields = ("amount_due", "paid_at")
