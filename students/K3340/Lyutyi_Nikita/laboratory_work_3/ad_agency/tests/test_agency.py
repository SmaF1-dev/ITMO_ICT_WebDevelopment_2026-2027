from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from ad_agency.models import (
    Advertiser, AdvertisingRequest, AdvertisingService, Contract,
    Employee, Material, MaterialUsageNorm, PaymentOrder, RequestWork, ServiceCategory,
)
from ad_agency.services import line_total, request_total


class AgencyApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.staff = user_model.objects.create_user("staff", password="StrongPassword!123", is_staff=True)
        cls.reader = user_model.objects.create_user("reader", password="StrongPassword!123")
        cls.advertiser = Advertiser.objects.create(name="ООО Тест")
        cls.employee = Employee.objects.create(first_name="Иван", last_name="Иванов", phone="+70000000001")
        cls.category = ServiceCategory.objects.create(name="Баннеры")
        cls.service = AdvertisingService.objects.create(
            category=cls.category, name="Печать", unit="м²", current_price=Decimal("5.00")
        )
        cls.material = Material.objects.create(name="Полотно", unit="м²")
        cls.norm = MaterialUsageNorm.objects.create(
            service=cls.service, material=cls.material, quantity_per_unit=Decimal("1.000")
        )
        cls.req = AdvertisingRequest.objects.create(
            advertiser=cls.advertiser, contact_person="Олег", contact_phone="+70000000002",
            contact_email="oleg@example.org"
        )
        cls.work1 = RequestWork.objects.create(
            request=cls.req, service=cls.service, employee=cls.employee,
            quantity=Decimal("0.001"), agreed_unit_price=Decimal("5.00")
        )
        cls.work2 = RequestWork.objects.create(
            request=cls.req, service=cls.service, employee=cls.employee,
            quantity=Decimal("0.001"), agreed_unit_price=Decimal("5.00")
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.staff)

    def test_round_each_work_before_sum(self):
        self.assertEqual(line_total(self.work1), Decimal("0.01"))
        self.assertEqual(request_total(self.req.pk), Decimal("0.02"))

    def test_json_response_declares_utf8_for_windows_powershell(self):
        response = self.client.get("/api/reports/services/", HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("charset=utf-8", response["Content-Type"].lower())
        self.assertIn("Баннеры", response.content.decode("utf-8"))

    def test_openapi_documentation_pages(self):
        self.client.force_authenticate(user=None)
        schema = self.client.get("/api/schema/")
        self.assertEqual(schema.status_code, 200)
        self.assertIn(b"openapi", schema.content)
        page = self.client.get("/api/docs/")
        self.assertEqual(page.status_code, 200)

    def test_token_required(self):
        self.client.force_authenticate(user=None)
        self.assertEqual(self.client.get("/api/advertisers/").status_code, 401)

    def test_reader_can_read_but_cannot_modify(self):
        self.client.force_authenticate(self.reader)
        self.assertEqual(self.client.get("/api/advertisers/").status_code, 200)
        self.assertEqual(self.client.post("/api/advertisers/", {"name": "Новый"}).status_code, 403)

    def test_nested_one_to_many(self):
        response = self.client.get(f"/api/advertisers/{self.advertiser.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["requests"]), 1)

    def test_nested_many_to_many(self):
        response = self.client.get(f"/api/services/{self.service.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["materials"][0]["name"], "Полотно")
        self.assertEqual(response.data["norms"][0]["quantity_per_unit"], "1.000")

    def test_missing_contact_rejected(self):
        response = self.client.post("/api/requests/", {
            "advertiser": self.advertiser.pk, "contact_person": " ",
            "contact_phone": "123", "contact_email": "test@example.org",
        })
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_rejected(self):
        response = self.client.post("/api/requests/", {
            "advertiser": self.advertiser.pk, "contact_person": "Иван",
            "contact_phone": "123", "contact_email": "not-an-email",
        })
        self.assertEqual(response.status_code, 400)

    def test_norm_uses_unique_pair(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MaterialUsageNorm.objects.create(
                    service=self.service, material=self.material,
                    quantity_per_unit=Decimal("2.000")
                )

    def test_models_use_exact_approved_table_names_and_primary_keys(self):
        expected = {
            Advertiser: ("advertiser", "advertiser_id"),
            Employee: ("employee", "employee_id"),
            ServiceCategory: ("service_category", "category_id"),
            AdvertisingService: ("advertising_service", "service_id"),
            Material: ("material", "material_id"),
            AdvertisingRequest: ("advertising_request", "request_id"),
            RequestWork: ("request_work", "work_id"),
            Contract: ("contract", "contract_id"),
            PaymentOrder: ("payment_order", "payment_order_id"),
        }
        for model, (table, pk_field) in expected.items():
            with self.subTest(table=table):
                self.assertEqual(model._meta.db_table, table)
                self.assertEqual(model._meta.pk.name, pk_field)
        self.assertEqual(MaterialUsageNorm._meta.db_table, "material_usage_norm")
        self.assertEqual({field.name for field in MaterialUsageNorm._meta.pk_fields}, {"service", "material"})
        self.assertFalse(any(field.name == "id" for field in MaterialUsageNorm._meta.local_fields))

    def test_composite_key_norm_detail_api(self):
        self.assertEqual(self.norm.pk, (self.service.pk, self.material.pk))
        path = f"/api/material-norms/{self.service.pk}-{self.material.pk}/"
        fetched = self.client.get(path)
        self.assertEqual(fetched.status_code, 200, fetched.data)
        self.assertEqual(fetched.data["key"], f"{self.service.pk}-{self.material.pk}")
        modified = self.client.patch(path, {"quantity_per_unit": "2.000"}, format="json")
        self.assertEqual(modified.status_code, 200, modified.data)
        self.norm.refresh_from_db()
        self.assertEqual(self.norm.quantity_per_unit, Decimal("2.000"))
        other = Material.objects.create(name="Лак", unit="л")
        rejected = self.client.patch(path, {"material": other.pk}, format="json")
        self.assertEqual(rejected.status_code, 400, rejected.data)

    def test_cannot_change_material_unit_with_norm(self):
        r = self.client.patch(f"/api/materials/{self.material.pk}/", {"unit": "кг"})
        self.assertEqual(r.status_code, 400)

    def test_cannot_change_service_unit_after_order(self):
        r = self.client.patch(f"/api/services/{self.service.pk}/", {"unit": "шт."})
        self.assertEqual(r.status_code, 400)

    def test_reject_invalid_quantities_and_prices(self):
        bad_work = self.client.post("/api/works/", {
            "request": self.req.pk, "service": self.service.pk,
            "employee": self.employee.pk, "quantity": "0.000",
            "agreed_unit_price": "10.00",
        })
        self.assertEqual(bad_work.status_code, 400)
        bad_price = self.client.post("/api/services/", {
            "category": self.category.pk, "name": "Новинка",
            "unit": "м²", "current_price": "-1.00"
        })
        self.assertEqual(bad_price.status_code, 400)
        bad_norm = self.client.post("/api/material-norms/", {
            "service": self.service.pk, "material": self.material.pk,
            "quantity_per_unit": "0.000"
        })
        self.assertEqual(bad_norm.status_code, 400)

    def test_duplicate_service_and_norm_rejected(self):
        duplicate_service = self.client.post("/api/services/", {
            "category": self.category.pk, "name": self.service.name,
            "unit": "шт.", "current_price": "5.00"
        })
        self.assertEqual(duplicate_service.status_code, 400)
        duplicate_norm = self.client.post("/api/material-norms/", {
            "service": self.service.pk, "material": self.material.pk,
            "quantity_per_unit": "2.000"
        })
        self.assertEqual(duplicate_norm.status_code, 400)

    def test_contract_requires_positive_total(self):
        req = AdvertisingRequest.objects.create(
            advertiser=self.advertiser, contact_person="Н", contact_phone="123",
            contact_email="free@example.org"
        )
        RequestWork.objects.create(request=req, service=self.service, employee=self.employee,
                                   quantity=Decimal("1.000"), agreed_unit_price=Decimal("0.00"))
        r = self.client.post("/api/contracts/", {
            "request": req.pk, "contract_number": "FREE-1", "signed_at": str(timezone.localdate())
        })
        self.assertEqual(r.status_code, 400)

    def test_contract_and_invoice(self):
        c = self.client.post("/api/contracts/", {
            "request": self.req.pk, "contract_number": "C-100", "signed_at": str(timezone.localdate())
        })
        self.assertEqual(c.status_code, 201, c.data)
        inv = self.client.post("/api/payment-orders/", {
            "contract": c.data["id"], "document_number": "P-100",
            "issued_at": str(timezone.localdate()), "amount_due": "100.00",
        })
        self.assertEqual(inv.status_code, 201, inv.data)
        self.assertEqual(inv.data["amount_due"], "0.02")
        return c.data["id"], inv.data["id"]

    def test_signed_work_locked(self):
        self.test_contract_and_invoice()
        r = self.client.patch(f"/api/works/{self.work1.pk}/", {"quantity": "2.000"})
        self.assertEqual(r.status_code, 400)
        r2 = self.client.delete(f"/api/works/{self.work1.pk}/")
        self.assertEqual(r2.status_code, 400)

    def test_mark_paid_and_reject_early_date(self):
        _, invoice_id = self.test_contract_and_invoice()
        bad = self.client.post(f"/api/payment-orders/{invoice_id}/mark-paid/", {
            "paid_at": str(timezone.localdate() - timedelta(days=1)),
        })
        self.assertEqual(bad.status_code, 400)
        good = self.client.post(f"/api/payment-orders/{invoice_id}/mark-paid/", {
            "paid_at": str(timezone.localdate()),
        })
        self.assertEqual(good.status_code, 200, good.data)
        self.assertTrue(good.data["is_paid"])
        delete = self.client.delete(f"/api/payment-orders/{invoice_id}/")
        self.assertEqual(delete.status_code, 400)

    def test_analytics(self):
        _, invoice_id = self.test_contract_and_invoice()
        self.client.post(f"/api/payment-orders/{invoice_id}/mark-paid/", {"paid_at": str(timezone.localdate())})
        paths = [
            "/api/reports/completed-works/", "/api/reports/payment-orders/",
            "/api/reports/services/", "/api/reports/advertiser-requests/",
            "/api/reports/employee-workload/", "/api/reports/quarterly/",
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 200)
        response = self.client.get("/api/reports/employee-workload/")
        row = next(v for v in response.data if v["employee_id"] == self.employee.pk)
        self.assertEqual(row["request_count"], 1)

    def test_period_inversion_is_error(self):
        r = self.client.get("/api/reports/completed-works/?date_from=2026-12-31&date_to=2026-01-01")
        self.assertEqual(r.status_code, 400)

    def test_staff_can_crud_catalog(self):
        r = self.client.post("/api/advertisers/", {"name": "ООО Второй"})
        self.assertEqual(r.status_code, 201)
        pk = r.data["id"]
        self.assertEqual(self.client.patch(f"/api/advertisers/{pk}/", {"name": "ООО Третий"}).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/advertisers/{pk}/").status_code, 204)


class DjoserAuthTests(TestCase):
    def test_registration_token_login_and_me(self):
        client = APIClient()
        r = client.post("/auth/users/", {
            "username": "new_client_1", "password": "StrongPassword!123",
            "re_password": "StrongPassword!123"
        }, format="json")
        self.assertEqual(r.status_code, 201, r.data)
        login = client.post("/auth/token/login/", {
            "username": "new_client_1", "password": "StrongPassword!123"
        }, format="json")
        self.assertEqual(login.status_code, 200, login.data)
        self.assertIn("auth_token", login.data)
        client.credentials(HTTP_AUTHORIZATION=f"Token {login.data['auth_token']}")
        me = client.get("/auth/users/me/")
        self.assertEqual(me.status_code, 200, me.data)
        self.assertEqual(me.data["username"], "new_client_1")
