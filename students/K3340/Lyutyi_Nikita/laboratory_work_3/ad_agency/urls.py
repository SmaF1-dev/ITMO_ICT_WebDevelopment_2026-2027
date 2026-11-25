from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import reports
from .views import (
    AdvertiserViewSet, AdvertisingRequestViewSet, AdvertisingServiceViewSet,
    ContractViewSet, EmployeeViewSet, MaterialUsageNormViewSet,
    MaterialViewSet, PaymentOrderViewSet, RequestWorkViewSet, ServiceCategoryViewSet,
)

router = DefaultRouter()
router.register("advertisers", AdvertiserViewSet)
router.register("employees", EmployeeViewSet)
router.register("categories", ServiceCategoryViewSet)
router.register("services", AdvertisingServiceViewSet)
router.register("materials", MaterialViewSet)
router.register("material-norms", MaterialUsageNormViewSet)
router.register("requests", AdvertisingRequestViewSet)
router.register("works", RequestWorkViewSet)
router.register("contracts", ContractViewSet)
router.register("payment-orders", PaymentOrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("reports/completed-works/", reports.completed_works),
    path("reports/payment-orders/", reports.payment_orders),
    path("reports/services/", reports.services_catalog),
    path("reports/advertiser-requests/", reports.advertiser_requests),
    path("reports/employee-workload/", reports.employee_workload),
    path("reports/quarterly/", reports.quarterly),
]
