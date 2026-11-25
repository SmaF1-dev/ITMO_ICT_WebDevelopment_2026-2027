from collections import defaultdict
from datetime import date
from decimal import Decimal

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema

from .report_schemas import (
    AdvertiserRequestResponse, CompletedWorkResponse, EmployeeWorkloadResponse,
    PaymentOrderResponse, QuarterlyResponse, ServiceCatalogResponse,
)

from .models import (
    Advertiser, AdvertisingRequest, AdvertisingService, Employee, PaymentOrder, RequestWork,
    ServiceCategory,
)
from .services import line_total


class PeriodInput(serializers.Serializer):
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

    def validate(self, attrs):
        if attrs.get("date_from") and attrs.get("date_to") and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("Начало периода не может быть позже конца.")
        return attrs


def period(request):
    form = PeriodInput(data=request.query_params)
    form.is_valid(raise_exception=True)
    return form.validated_data


def by_dates(queryset, field, dates):
    if "date_from" in dates:
        queryset = queryset.filter(**{f"{field}__gte": dates["date_from"]})
    if "date_to" in dates:
        queryset = queryset.filter(**{f"{field}__lte": dates["date_to"]})
    return queryset


@extend_schema(summary="Выполненные работы", tags=["Аналитика"], parameters=[PeriodInput], responses=CompletedWorkResponse(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def completed_works(request):
    """Задание 1: оплаченные работы, исполнитель, услуга, заказчик и дата оплаты."""
    works = RequestWork.objects.select_related(
        "employee", "service", "request__advertiser", "request__contract__payment_order"
    ).filter(request__contract__payment_order__paid_at__isnull=False)
    works = by_dates(works, "request__contract__payment_order__paid_at", period(request))
    data = [{
        "work_id": w.pk,
        "paid_at": str(w.request.contract.payment_order.paid_at),
        "advertiser": w.request.advertiser.name,
        "service_id": w.service_id,
        "service": w.service.name,
        "employee_last_name": w.employee.last_name,
        "quantity": str(w.quantity),
        "cost": str(line_total(w)),
    } for w in works.order_by("pk")]
    return Response(data)


@extend_schema(summary="Платёжные поручения", tags=["Аналитика"], parameters=[PeriodInput], responses=PaymentOrderResponse(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_orders(request):
    """Задание 2: поручения за период без умножения суммы при JOIN с работами."""
    orders = PaymentOrder.objects.select_related(
        "contract__request__advertiser"
    ).prefetch_related("contract__request__works__service")
    orders = by_dates(orders, "issued_at", period(request))
    return Response([{
        "id": order.pk,
        "number": order.document_number,
        "issued_at": str(order.issued_at),
        "advertiser": order.contract.request.advertiser.name,
        "services": sorted(set(w.service.name for w in order.contract.request.works.all())),
        "paid": order.paid_at is not None,
        "paid_at": str(order.paid_at) if order.paid_at else None,
        "amount_due": str(order.amount_due),
    } for order in orders.order_by("issued_at", "pk")])


@extend_schema(summary="Прайс-лист по категориям", tags=["Аналитика"], responses=ServiceCatalogResponse(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def services_catalog(request):
    """Задание 3: прайс-лист по категориям."""
    categories = ServiceCategory.objects.prefetch_related("services").order_by("name")
    return Response([{
        "category": cat.name,
        "services": [{
            "id": s.pk, "name": s.name, "unit": s.unit, "price": str(s.current_price)
        } for s in cat.services.all()]
    } for cat in categories])


@extend_schema(summary="Заключённые заявки", tags=["Аналитика"], parameters=[PeriodInput, OpenApiParameter(name="advertiser_id", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description="ID рекламодателя")], responses=AdvertiserRequestResponse(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def advertiser_requests(request):
    """Задание 4: заключённые заявки по дате договора."""
    dates = period(request)
    query = AdvertisingRequest.objects.filter(contract__isnull=False).select_related("advertiser", "contract")
    advertiser_id = request.query_params.get("advertiser_id")
    if advertiser_id:
        if not advertiser_id.isdigit() or int(advertiser_id) <= 0:
            raise serializers.ValidationError({"advertiser_id": "Укажите положительный целый ID."})
        query = query.filter(advertiser_id=int(advertiser_id))
    query = by_dates(query, "contract__signed_at", dates)
    return Response([{
        "request_id": obj.pk,
        "advertiser": obj.advertiser.name,
        "submitted_at": obj.submitted_at.isoformat(),
        "contract_number": obj.contract.contract_number,
        "signed_at": str(obj.contract.signed_at),
    } for obj in query.order_by("contract__signed_at", "pk")])


@extend_schema(summary="Количество заявок сотрудников", tags=["Аналитика"], parameters=[PeriodInput], responses=EmployeeWorkloadResponse(many=True))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def employee_workload(request):
    """Задание 5: число разных оплаченных заявок каждого сотрудника."""
    dates = period(request)
    restriction = Q(request_works__request__contract__payment_order__paid_at__isnull=False)
    if "date_from" in dates:
        restriction &= Q(request_works__request__contract__payment_order__paid_at__gte=dates["date_from"])
    if "date_to" in dates:
        restriction &= Q(request_works__request__contract__payment_order__paid_at__lte=dates["date_to"])
    employees = Employee.objects.annotate(
        request_count=Count("request_works__request_id", filter=restriction, distinct=True)
    ).order_by("last_name", "first_name", "pk")
    return Response([{
        "employee_id": e.pk,
        "employee": str(e),
        "request_count": e.request_count,
    } for e in employees])


def last_complete_quarter(today):
    year = today.year
    quarter = (today.month - 1) // 3
    if quarter == 0:
        return year - 1, 4
    return year, quarter


def quarter_dates(year, quarter):
    start = date(year, (quarter - 1) * 3 + 1, 1)
    if quarter == 4:
        return start, date(year + 1, 1, 1)
    return start, date(year, quarter * 3 + 1, 1)


@extend_schema(summary="Квартальный отчёт", tags=["Аналитика"], parameters=[OpenApiParameter(name="year", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description="Год, например 2026"), OpenApiParameter(name="quarter", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, required=False, description="Квартал от 1 до 4")], responses=QuarterlyResponse)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def quarterly(request):
    """Квартальный отчёт: сумма округлённых строк у каждого исполнителя."""
    today = timezone.localdate()
    default_year, default_quarter = last_complete_quarter(today)
    raw_year = request.query_params.get("year", str(default_year))
    raw_quarter = request.query_params.get("quarter", str(default_quarter))
    if not raw_year.isdigit() or not raw_quarter.isdigit():
        raise serializers.ValidationError("Год и квартал должны быть числами.")
    year, q = int(raw_year), int(raw_quarter)
    if year < 2000 or year > 9998 or q not in (1, 2, 3, 4):
        raise serializers.ValidationError("Некорректный год или квартал.")
    start, end = quarter_dates(year, q)
    works = RequestWork.objects.filter(
        request__contract__payment_order__paid_at__gte=start,
        request__contract__payment_order__paid_at__lt=end,
    ).select_related("employee", "service", "request").order_by("employee__last_name", "pk")
    totals = defaultdict(lambda: {"amount": Decimal("0.00"), "requests": set(), "works": []})
    for w in works:
        item = totals[w.employee_id]
        item["name"] = str(w.employee)
        item["amount"] += line_total(w)
        item["requests"].add(w.request_id)
        item["works"].append({"work_id": w.pk, "service": w.service.name, "cost": str(line_total(w))})
    employees = [{
        "employee_id": pk,
        "employee": item["name"],
        "requests": len(item["requests"]),
        "amount": str(item["amount"]),
        "works": item["works"],
    } for pk, item in sorted(totals.items())]
    grand_total = sum((v["amount"] for v in totals.values()), Decimal("0.00"))
    return Response({
        "year": year, "quarter": q,
        "start_date": str(start), "end_exclusive": str(end),
        "employees": employees, "total": str(grand_total),
    })
