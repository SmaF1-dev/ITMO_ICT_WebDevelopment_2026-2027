from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Advertiser, AdvertisingRequest, AdvertisingService, Contract, Employee,
    Material, MaterialUsageNorm, PaymentOrder, RequestWork, ServiceCategory,
)
from .permissions import StaffWritePermission
from .serializers import (
    AdvertiserDetailSerializer, AdvertiserSerializer, AdvertisingRequestNestedSerializer,
    AdvertisingRequestSerializer, AdvertisingServiceDetailSerializer,
    AdvertisingServiceSerializer, ContractSerializer, EmployeeSerializer,
    MarkPaidSerializer, MaterialSerializer, MaterialUsageNormSerializer,
    PaymentOrderSerializer, RequestWorkSerializer, ServiceCategorySerializer,
)
from .services import (
    lock_requests, require_editable, validate_contract, validate_payment,
    refuse_paid_delete,
)


class StaffModelViewSet(viewsets.ModelViewSet):
    permission_classes = [StaffWritePermission]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError("Запись используется в других таблицах и не может быть удалена.")


class AdvertiserViewSet(StaffModelViewSet):
    queryset = Advertiser.objects.all()
    serializer_class = AdvertiserSerializer
    search_fields = ["name"]
    ordering_fields = ["name", "pk"]

    def get_serializer_class(self):
        return AdvertiserDetailSerializer if self.action == "retrieve" else AdvertiserSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("requests") if self.action == "retrieve" else qs


class EmployeeViewSet(StaffModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["last_name", "first_name", "pk"]


class ServiceCategoryViewSet(StaffModelViewSet):
    queryset = ServiceCategory.objects.all()
    serializer_class = ServiceCategorySerializer
    search_fields = ["name"]


class AdvertisingServiceViewSet(StaffModelViewSet):
    queryset = AdvertisingService.objects.select_related("category")
    serializer_class = AdvertisingServiceSerializer
    search_fields = ["name", "category__name"]
    ordering_fields = ["name", "current_price", "pk"]

    def get_serializer_class(self):
        return AdvertisingServiceDetailSerializer if self.action == "retrieve" else AdvertisingServiceSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == "retrieve":
            qs = qs.prefetch_related("materials", "norms__material")
        return qs

    def perform_update(self, serializer):
        with transaction.atomic():
            service = AdvertisingService.objects.select_for_update().get(pk=serializer.instance.pk)
            if "unit" in serializer.validated_data and service.unit != serializer.validated_data["unit"]:
                if service.request_works.exists():
                    raise serializers.ValidationError("Единицу ранее использованной услуги нельзя менять.")
            serializer.save()


class MaterialViewSet(StaffModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    search_fields = ["name"]

    def perform_update(self, serializer):
        with transaction.atomic():
            material = Material.objects.select_for_update().get(pk=serializer.instance.pk)
            if "unit" in serializer.validated_data and material.unit != serializer.validated_data["unit"]:
                if material.norms.exists():
                    raise serializers.ValidationError("Нельзя менять единицу материала с нормами расхода.")
            serializer.save()


class MaterialUsageNormViewSet(StaffModelViewSet):
    queryset = MaterialUsageNorm.objects.select_related("service", "material")
    serializer_class = MaterialUsageNormSerializer
    lookup_value_regex = r"[0-9]+-[0-9]+"

    def get_object(self):
        # Unlike the other models this one has a composite primary key.
        raw_key = self.kwargs[self.lookup_field]
        service_id, material_id = (int(part) for part in raw_key.split("-"))
        instance = get_object_or_404(self.get_queryset(), service_id=service_id, material_id=material_id)
        self.check_object_permissions(self.request, instance)
        return instance


class AdvertisingRequestViewSet(StaffModelViewSet):
    queryset = AdvertisingRequest.objects.select_related("advertiser")
    serializer_class = AdvertisingRequestSerializer
    search_fields = ["advertiser__name", "contact_person"]
    ordering_fields = ["submitted_at", "pk"]

    def get_serializer_class(self):
        return AdvertisingRequestNestedSerializer if self.action == "retrieve" else AdvertisingRequestSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related("works__service", "works__employee") if self.action == "retrieve" else qs

    def perform_update(self, serializer):
        with transaction.atomic():
            lock_requests(serializer.instance.pk)
            require_editable(serializer.instance.pk)
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            lock_requests(instance.pk)
            require_editable(instance.pk)
            super().perform_destroy(instance)


class RequestWorkViewSet(StaffModelViewSet):
    queryset = RequestWork.objects.select_related("request", "service", "employee")
    serializer_class = RequestWorkSerializer
    search_fields = ["service__name", "employee__last_name"]

    def perform_create(self, serializer):
        with transaction.atomic():
            req_id = serializer.validated_data["request"].pk
            lock_requests(req_id)
            require_editable(req_id)
            serializer.save()

    def perform_update(self, serializer):
        with transaction.atomic():
            req_ids = [serializer.instance.request_id]
            new_req = serializer.validated_data.get("request")
            if new_req is not None:
                req_ids.append(new_req.pk)
            lock_requests(*req_ids)
            for req_id in req_ids:
                require_editable(req_id)
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            lock_requests(instance.request_id)
            require_editable(instance.request_id)
            super().perform_destroy(instance)


class ContractViewSet(StaffModelViewSet):
    queryset = Contract.objects.select_related("request", "request__advertiser")
    serializer_class = ContractSerializer
    search_fields = ["contract_number"]

    def perform_create(self, serializer):
        with transaction.atomic():
            req_id = serializer.validated_data["request"].pk
            lock_requests(req_id)
            validate_contract(req_id, serializer.validated_data["signed_at"])
            if Contract.objects.filter(request_id=req_id).exists():
                raise serializers.ValidationError("Для заявки уже существует договор.")
            serializer.save()

    def perform_update(self, serializer):
        raise serializers.ValidationError("Подписанный договор не изменяется. Создайте новую заявку.")

    def perform_destroy(self, instance):
        raise serializers.ValidationError("Подписанный договор и история заказов не удаляются.")


class PaymentOrderViewSet(StaffModelViewSet):
    queryset = PaymentOrder.objects.select_related("contract", "contract__request")
    serializer_class = PaymentOrderSerializer
    search_fields = ["document_number", "contract__contract_number"]
    ordering_fields = ["issued_at", "paid_at", "amount_due", "pk"]

    def perform_create(self, serializer):
        with transaction.atomic():
            contract = serializer.validated_data["contract"]
            lock_requests(contract.request_id)
            contract = Contract.objects.select_for_update().get(pk=contract.pk)
            if PaymentOrder.objects.filter(contract_id=contract.pk).exists():
                raise serializers.ValidationError("Для договора уже выставлено поручение.")
            total = validate_payment(contract, serializer.validated_data["issued_at"])
            serializer.save(amount_due=total)

    def perform_update(self, serializer):
        with transaction.atomic():
            order = PaymentOrder.objects.select_for_update().get(pk=serializer.instance.pk)
            if order.paid_at is not None:
                raise serializers.ValidationError("Оплаченное поручение изменять нельзя.")
            contract = serializer.validated_data.get("contract", order.contract)
            if contract.pk != order.contract_id:
                raise serializers.ValidationError("Переносить поручение на другой договор нельзя.")
            validate_payment(contract, serializer.validated_data.get("issued_at", order.issued_at))
            serializer.save()

    def perform_destroy(self, instance):
        with transaction.atomic():
            order = PaymentOrder.objects.select_for_update().get(pk=instance.pk)
            refuse_paid_delete(order)
            order.delete()

    @action(detail=True, methods=["post"], url_path="mark-paid", permission_classes=[StaffWritePermission])
    def mark_paid(self, request, pk=None):
        if not request.user.is_staff:
            return Response({"detail": "Недостаточно прав."}, status=status.HTTP_403_FORBIDDEN)
        data = MarkPaidSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            order = PaymentOrder.objects.select_for_update().get(pk=self.get_object().pk)
            if order.paid_at is not None:
                raise serializers.ValidationError("Платёж уже отмечен оплаченным.")
            date_paid = data.validated_data["paid_at"]
            if date_paid < order.issued_at:
                raise serializers.ValidationError({"paid_at": "Оплата не может быть раньше выставления поручения."})
            order.paid_at = date_paid
            order.save(update_fields=["paid_at"])
        return Response(PaymentOrderSerializer(order).data)
