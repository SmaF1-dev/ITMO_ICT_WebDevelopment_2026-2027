from datetime import date, timedelta, datetime, time
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from ad_agency.models import (
    Advertiser, AdvertisingRequest, AdvertisingService, Contract,
    Employee, Material, MaterialUsageNorm, PaymentOrder, RequestWork, ServiceCategory,
)
from ad_agency.reports import last_complete_quarter, quarter_dates
from ad_agency.services import request_total


class Command(BaseCommand):
    help = "Создать демонстрационные данные для API и аналитики (повторный запуск безопасен)."

    @transaction.atomic
    def handle(self, *args, **options):
        category, _ = ServiceCategory.objects.get_or_create(name="Демо — наружная реклама")
        service1, _ = AdvertisingService.objects.get_or_create(
            category=category, name="Демо — печать баннеров (м²)",
            defaults={"unit": "м²", "current_price": Decimal("750.00")},
        )
        service2, _ = AdvertisingService.objects.get_or_create(
            category=category, name="Демо — дизайн макета (час)",
            defaults={"unit": "час", "current_price": Decimal("500.00")},
        )
        material, _ = Material.objects.get_or_create(name="Демо — баннерная ткань", defaults={"unit": "м²"})
        MaterialUsageNorm.objects.get_or_create(
            service=service1, material=material, defaults={"quantity_per_unit": Decimal("1.000")}
        )
        customer, _ = Advertiser.objects.get_or_create(name="Демо — ООО Север")
        employee1, _ = Employee.objects.get_or_create(
            first_name="Иван", last_name="Демо-Петров", defaults={"phone": "+79990000001", "email": "ivan@example.test"}
        )
        employee2, _ = Employee.objects.get_or_create(
            first_name="Анна", last_name="Демо-Соколова", defaults={"phone": "+79990000002", "email": "anna@example.test"}
        )
        req = AdvertisingRequest.objects.filter(contact_email="agency-demo-1@example.test").first()
        if req is None:
            req = AdvertisingRequest.objects.create(
                advertiser=customer, contact_person="Олег Климов", contact_phone="+79990000003",
                contact_email="agency-demo-1@example.test",
            )
        year, quarter = last_complete_quarter(timezone.localdate())
        start, end = quarter_dates(year, quarter)
        signed = start + timedelta(days=3)
        submitted = signed - timedelta(days=1)
        AdvertisingRequest.objects.filter(pk=req.pk).update(
            submitted_at=timezone.make_aware(datetime.combine(submitted, time.min))
        )
        RequestWork.objects.get_or_create(
            request=req, service=service1, employee=employee1,
            defaults={"quantity": Decimal("2.000"), "agreed_unit_price": Decimal("750.00")},
        )
        RequestWork.objects.get_or_create(
            request=req, service=service2, employee=employee2,
            defaults={"quantity": Decimal("1.000"), "agreed_unit_price": Decimal("500.00")},
        )
        contract, _ = Contract.objects.get_or_create(
            request=req, defaults={"contract_number": "DEMO-CONTRACT-001", "signed_at": signed}
        )
        PaymentOrder.objects.get_or_create(
            contract=contract,
            defaults={
                "document_number": "DEMO-PAY-001", "issued_at": signed,
                "amount_due": request_total(req.pk), "paid_at": signed + timedelta(days=1),
            },
        )
        req2 = AdvertisingRequest.objects.filter(contact_email="agency-demo-2@example.test").first()
        if req2 is None:
            req2 = AdvertisingRequest.objects.create(
                advertiser=customer, contact_person="Олег Климов", contact_phone="+79990000003",
                contact_email="agency-demo-2@example.test",
            )
        RequestWork.objects.get_or_create(
            request=req2, service=service1, employee=employee2,
            defaults={"quantity": Decimal("3.000"), "agreed_unit_price": Decimal("750.00")},
        )
        contract2, _ = Contract.objects.get_or_create(
            request=req2, defaults={"contract_number": "DEMO-CONTRACT-002", "signed_at": timezone.localdate()}
        )
        PaymentOrder.objects.get_or_create(
            contract=contract2,
            defaults={
                "document_number": "DEMO-PAY-002", "issued_at": timezone.localdate(),
                "amount_due": request_total(req2.pk), "paid_at": None,
            },
        )
        self.stdout.write(self.style.SUCCESS("Демо-данные готовы: 2 заявки, 2 договора, 2 поручения."))
