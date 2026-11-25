from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import AdvertisingRequest, Contract, PaymentOrder, RequestWork

KOP = Decimal("0.01")


def line_total(work):
    """Денежная сумма строки: округляем именно строку, не общий итог."""
    return (work.quantity * work.agreed_unit_price).quantize(KOP, rounding=ROUND_HALF_UP)


def request_total(request_id):
    works = RequestWork.objects.filter(request_id=request_id).only("quantity", "agreed_unit_price")
    return sum((line_total(work) for work in works), Decimal("0.00"))


def lock_requests(*ids):
    """Одинаковый порядок блокировки строк снижает вероятность deadlock."""
    keys = sorted(set(pk for pk in ids if pk is not None))
    return list(AdvertisingRequest.objects.select_for_update().filter(pk__in=keys).order_by("pk"))


def require_editable(request_id):
    if Contract.objects.filter(request_id=request_id).exists():
        raise ValidationError("Работы и данные заявки нельзя менять после заключения договора.")


def validate_contract(request_id, signed_at):
    request = AdvertisingRequest.objects.get(pk=request_id)
    if signed_at < timezone.localtime(request.submitted_at).date():
        raise ValidationError({"signed_at": "Договор не может быть подписан до подачи заявки."})
    total = request_total(request_id)
    if total <= 0:
        raise ValidationError("Для договора нужна хотя бы одна платная работа и положительная стоимость заявки.")
    return total


def validate_payment(contract, issued_at):
    if issued_at < contract.signed_at:
        raise ValidationError({"issued_at": "Поручение не может предшествовать договору."})
    total = request_total(contract.request_id)
    if total <= 0:
        raise ValidationError("Сумма платёжного поручения должна быть положительной.")
    return total


def refuse_paid_delete(order):
    if order.paid_at is not None:
        raise ValidationError("Оплаченное платёжное поручение удалять нельзя.")


def has_payment(request_id):
    return PaymentOrder.objects.filter(contract__request_id=request_id).exists()
