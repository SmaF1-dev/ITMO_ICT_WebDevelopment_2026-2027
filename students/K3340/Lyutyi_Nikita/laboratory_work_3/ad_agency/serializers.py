from decimal import Decimal

from rest_framework import serializers

from .models import (
    Advertiser, AdvertisingRequest, AdvertisingService, Contract, Employee,
    Material, MaterialUsageNorm, PaymentOrder, RequestWork, ServiceCategory,
)
from .services import request_total


class AdvertiserSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = Advertiser
        fields = ["id", "name"]


class EmployeeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = Employee
        fields = ["id", "first_name", "last_name", "phone", "email"]


class ServiceCategorySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = ServiceCategory
        fields = ["id", "name"]


class MaterialSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = Material
        fields = ["id", "name", "unit"]

    def validate(self, attrs):
        if self.instance and "unit" in attrs and attrs["unit"] != self.instance.unit:
            if self.instance.norms.exists():
                raise serializers.ValidationError({"unit": "Единицу материала с установленными нормами нельзя менять."})
        return attrs


class MaterialUsageNormSerializer(serializers.ModelSerializer):
    key = serializers.SerializerMethodField()

    def get_key(self, obj):
        return f"{obj.service_id}-{obj.material_id}"

    class Meta:
        model = MaterialUsageNorm
        fields = ["key", "service", "material", "quantity_per_unit"]

    def validate(self, attrs):
        quantity = attrs.get("quantity_per_unit", getattr(self.instance, "quantity_per_unit", None))
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity_per_unit": "Норма расхода должна быть больше нуля."})
        service = attrs.get("service", getattr(self.instance, "service", None))
        material = attrs.get("material", getattr(self.instance, "material", None))
        if self.instance:
            if service and service.pk != self.instance.service_id:
                raise serializers.ValidationError({"service": "Связанные услуга и материал составляют первичный ключ и не изменяются."})
            if material and material.pk != self.instance.material_id:
                raise serializers.ValidationError({"material": "Для другой пары создайте новую норму расхода."})
        if service and material:
            same = MaterialUsageNorm.objects.filter(service=service, material=material)
            if self.instance:
                same = same.exclude(pk=self.instance.pk)
            if same.exists():
                raise serializers.ValidationError("Для этой пары услуги и материала норма уже существует.")
        return attrs


class MaterialUsageNormDetailSerializer(serializers.ModelSerializer):
    material = MaterialSerializer(read_only=True)

    class Meta:
        model = MaterialUsageNorm
        fields = ["material", "quantity_per_unit"]


class AdvertisingServiceSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = AdvertisingService
        fields = ["id", "category", "name", "unit", "current_price"]

    def validate(self, attrs):
        price = attrs.get("current_price", getattr(self.instance, "current_price", None))
        if price is not None and price < 0:
            raise serializers.ValidationError({"current_price": "Цена не может быть отрицательной."})
        category = attrs.get("category", getattr(self.instance, "category", None))
        name = attrs.get("name", getattr(self.instance, "name", None))
        if category and name:
            same = AdvertisingService.objects.filter(category=category, name=name)
            if self.instance:
                same = same.exclude(pk=self.instance.pk)
            if same.exists():
                raise serializers.ValidationError("В этой категории уже есть услуга с таким названием.")
        if self.instance and "unit" in attrs and attrs["unit"] != self.instance.unit:
            if self.instance.request_works.exists():
                raise serializers.ValidationError({"unit": "Единицу услуги, использованной в заказах, менять нельзя."})
        return attrs


class AdvertisingServiceDetailSerializer(AdvertisingServiceSerializer):
    materials = MaterialSerializer(many=True, read_only=True)
    norms = MaterialUsageNormDetailSerializer(many=True, read_only=True)

    class Meta(AdvertisingServiceSerializer.Meta):
        fields = AdvertisingServiceSerializer.Meta.fields + ["materials", "norms"]


class RequestWorkSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = RequestWork
        fields = ["id", "request", "service", "employee", "quantity", "agreed_unit_price"]

    def validate(self, attrs):
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        price = attrs.get("agreed_unit_price", getattr(self.instance, "agreed_unit_price", None))
        if quantity is not None and quantity <= 0:
            raise serializers.ValidationError({"quantity": "Количество должно быть больше нуля."})
        if price is not None and price < 0:
            raise serializers.ValidationError({"agreed_unit_price": "Цена не может быть отрицательной."})
        request = attrs.get("request", getattr(self.instance, "request", None))
        if request and Contract.objects.filter(request_id=request.pk).exists():
            raise serializers.ValidationError("После подписания договора работы не изменяются.")
        service = attrs.get("service", getattr(self.instance, "service", None))
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", None))
        if service and quantity is not None and service.unit.lower().strip() in {"шт", "шт.", "ед.", "экз."}:
            if quantity != quantity.to_integral_value():
                raise serializers.ValidationError({"quantity": "Для штучной услуги укажите целое количество."})
        return attrs


class RequestWorkNestedSerializer(RequestWorkSerializer):
    service = AdvertisingServiceSerializer(read_only=True)
    employee = EmployeeSerializer(read_only=True)

    class Meta(RequestWorkSerializer.Meta):
        fields = ["id", "service", "employee", "quantity", "agreed_unit_price"]


class AdvertisingRequestSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = AdvertisingRequest
        fields = ["id", "advertiser", "submitted_at", "contact_person", "contact_phone", "contact_email"]
        read_only_fields = ["submitted_at"]

    def validate(self, attrs):
        for field in ("contact_person", "contact_phone", "contact_email"):
            value = attrs.get(field, getattr(self.instance, field, ""))
            if not value or not value.strip():
                raise serializers.ValidationError({field: "Контактные данные должны быть заполнены."})
        if self.instance and Contract.objects.filter(request_id=self.instance.pk).exists():
            raise serializers.ValidationError("Подписанную заявку нельзя редактировать.")
        return attrs


class AdvertisingRequestNestedSerializer(AdvertisingRequestSerializer):
    works = RequestWorkNestedSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta(AdvertisingRequestSerializer.Meta):
        fields = AdvertisingRequestSerializer.Meta.fields + ["works", "total"]

    def get_total(self, obj):
        return str(request_total(obj.pk))


class AdvertiserDetailSerializer(AdvertiserSerializer):
    requests = AdvertisingRequestSerializer(many=True, read_only=True)

    class Meta(AdvertiserSerializer.Meta):
        fields = ["id", "name", "requests"]


class ContractSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = Contract
        fields = ["id", "request", "contract_number", "signed_at", "terms"]


class PaymentOrderSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="pk", read_only=True)

    is_paid = serializers.SerializerMethodField()

    class Meta:
        model = PaymentOrder
        fields = ["id", "contract", "document_number", "issued_at", "amount_due", "paid_at", "is_paid"]
        read_only_fields = ["amount_due", "paid_at", "is_paid"]

    def get_is_paid(self, obj):
        return obj.paid_at is not None


class MarkPaidSerializer(serializers.Serializer):
    paid_at = serializers.DateField(required=True)
