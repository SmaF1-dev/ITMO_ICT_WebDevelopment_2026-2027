from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


UNIT_CHOICES = [
    ("шт.", "штук"),
    ("м²", "квадратных метров"),
    ("час", "часов"),
    ("м", "метров"),
    ("пог. м", "погонных метров"),
    ("кг", "килограммов"),
    ("г", "граммов"),
    ("л", "литров"),
    ("мл", "миллилитров"),
    ("м³", "кубических метров"),
    ("ед.", "единиц"),
    ("экз.", "экземпляров"),
]


class Advertiser(models.Model):
    advertiser_id = models.BigAutoField(primary_key=True)
    name = models.CharField("Рекламодатель", max_length=255)

    class Meta:
        db_table = "advertiser"
        ordering = ["name", "pk"]
        verbose_name = "Рекламодатель"
        verbose_name_plural = "Рекламодатели"

    def __str__(self):
        return self.name


class Employee(models.Model):
    employee_id = models.BigAutoField(primary_key=True)
    first_name = models.CharField("Имя", max_length=100)
    last_name = models.CharField("Фамилия", max_length=100)
    phone = models.CharField("Телефон", max_length=30)
    email = models.EmailField("Электронная почта", blank=True, null=True)

    class Meta:
        db_table = "employee"
        ordering = ["last_name", "first_name", "pk"]
        verbose_name = "Исполнитель"
        verbose_name_plural = "Исполнители"

    def __str__(self):
        return f"{self.last_name} {self.first_name}"


class ServiceCategory(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    name = models.CharField("Категория", max_length=150, unique=True)

    class Meta:
        db_table = "service_category"
        ordering = ["name"]
        verbose_name = "Категория услуг"
        verbose_name_plural = "Категории услуг"

    def __str__(self):
        return self.name


class AdvertisingService(models.Model):
    service_id = models.BigAutoField(primary_key=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.PROTECT, related_name="services")
    name = models.CharField("Услуга", max_length=255)
    unit = models.CharField("Единица измерения", max_length=20, choices=UNIT_CHOICES)
    current_price = models.DecimalField("Цена по прайс-листу", max_digits=12, decimal_places=2)
    materials = models.ManyToManyField("Material", through="MaterialUsageNorm", related_name="services")

    class Meta:
        db_table = "advertising_service"
        ordering = ["category__name", "name", "pk"]
        constraints = [
            models.UniqueConstraint(fields=["category", "name"], name="uniq_service_in_category"),
            models.CheckConstraint(check=Q(current_price__gte=0), name="ck_service_nonnegative_price"),
        ]
        verbose_name = "Рекламная услуга"
        verbose_name_plural = "Рекламные услуги"

    def __str__(self):
        return self.name


class Material(models.Model):
    material_id = models.BigAutoField(primary_key=True)
    name = models.CharField("Материал", max_length=255, unique=True)
    unit = models.CharField("Единица измерения", max_length=20, choices=UNIT_CHOICES)

    class Meta:
        db_table = "material"
        ordering = ["name"]
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"

    def __str__(self):
        return self.name


class MaterialUsageNorm(models.Model):
    pk = models.CompositePrimaryKey("service_id", "material_id")
    service = models.ForeignKey(AdvertisingService, on_delete=models.CASCADE, related_name="norms")
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name="norms")
    quantity_per_unit = models.DecimalField("Норма расхода", max_digits=12, decimal_places=3)

    class Meta:
        db_table = "material_usage_norm"
        constraints = [
            models.CheckConstraint(check=Q(quantity_per_unit__gt=0), name="ck_norm_quantity_positive"),
        ]
        verbose_name = "Норма расхода материала"
        verbose_name_plural = "Нормы расхода материалов"

    def __str__(self):
        return f"{self.service} — {self.material}"


class AdvertisingRequest(models.Model):
    request_id = models.BigAutoField(primary_key=True)
    advertiser = models.ForeignKey(Advertiser, on_delete=models.PROTECT, related_name="requests")
    submitted_at = models.DateTimeField("Дата подачи", default=timezone.now, editable=False)
    contact_person = models.CharField("Контактное лицо", max_length=150)
    contact_phone = models.CharField("Телефон", max_length=30)
    contact_email = models.EmailField("Электронная почта")

    class Meta:
        db_table = "advertising_request"
        ordering = ["-submitted_at", "-pk"]
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"

    def clean(self):
        super().clean()
        for field in ("contact_person", "contact_phone", "contact_email"):
            if not (getattr(self, field) or "").strip():
                raise ValidationError({field: "Поле не должно быть пустым."})

    def __str__(self):
        return f"Заявка #{self.pk or 'новая'} ({self.advertiser})"


class RequestWork(models.Model):
    work_id = models.BigAutoField(primary_key=True)
    request = models.ForeignKey(AdvertisingRequest, on_delete=models.CASCADE, related_name="works")
    service = models.ForeignKey(AdvertisingService, on_delete=models.PROTECT, related_name="request_works")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="request_works")
    quantity = models.DecimalField("Количество", max_digits=12, decimal_places=3)
    agreed_unit_price = models.DecimalField("Согласованная цена", max_digits=12, decimal_places=2)

    class Meta:
        db_table = "request_work"
        ordering = ["pk"]
        constraints = [
            models.CheckConstraint(check=Q(quantity__gt=0), name="ck_work_quantity_positive"),
            models.CheckConstraint(check=Q(agreed_unit_price__gte=0), name="ck_work_nonnegative_price"),
        ]
        verbose_name = "Строка работы"
        verbose_name_plural = "Работы по заявкам"

    def __str__(self):
        return f"{self.service} — {self.quantity} ({self.employee})"


class Contract(models.Model):
    contract_id = models.BigAutoField(primary_key=True)
    request = models.OneToOneField(AdvertisingRequest, on_delete=models.PROTECT, related_name="contract")
    contract_number = models.CharField("Номер договора", max_length=50, unique=True)
    signed_at = models.DateField("Дата подписания")
    terms = models.TextField("Условия", blank=True, null=True)

    class Meta:
        db_table = "contract"
        ordering = ["-signed_at", "-pk"]
        verbose_name = "Договор"
        verbose_name_plural = "Договоры"

    def __str__(self):
        return self.contract_number


class PaymentOrder(models.Model):
    payment_order_id = models.BigAutoField(primary_key=True)
    contract = models.OneToOneField(Contract, on_delete=models.PROTECT, related_name="payment_order")
    document_number = models.CharField("Номер поручения", max_length=50, unique=True)
    issued_at = models.DateField("Дата выставления")
    amount_due = models.DecimalField("Сумма, ₽", max_digits=14, decimal_places=2)
    paid_at = models.DateField("Дата полной оплаты", null=True, blank=True)

    class Meta:
        db_table = "payment_order"
        ordering = ["-issued_at", "-pk"]
        constraints = [
            models.CheckConstraint(check=Q(amount_due__gt=0), name="ck_payment_amount_positive"),
            models.CheckConstraint(check=Q(paid_at__isnull=True) | Q(paid_at__gte=models.F("issued_at")), name="ck_paid_not_before_issued"),
        ]
        verbose_name = "Платёжное поручение"
        verbose_name_plural = "Платёжные поручения"

    def __str__(self):
        return self.document_number
