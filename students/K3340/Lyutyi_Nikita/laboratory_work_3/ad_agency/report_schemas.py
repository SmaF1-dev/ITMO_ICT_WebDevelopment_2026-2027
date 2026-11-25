"""OpenAPI response schemas for the six analytical endpoints.

These serializers describe response shapes; the report calculations remain in reports.py.
"""

from rest_framework import serializers


class CompletedWorkResponse(serializers.Serializer):
    work_id = serializers.IntegerField()
    paid_at = serializers.DateField()
    advertiser = serializers.CharField()
    service_id = serializers.IntegerField()
    service = serializers.CharField()
    employee_last_name = serializers.CharField()
    quantity = serializers.CharField()
    cost = serializers.CharField()


class PaymentOrderResponse(serializers.Serializer):
    id = serializers.IntegerField()
    number = serializers.CharField()
    issued_at = serializers.DateField()
    advertiser = serializers.CharField()
    services = serializers.ListField(child=serializers.CharField())
    paid = serializers.BooleanField()
    paid_at = serializers.DateField(allow_null=True)
    amount_due = serializers.CharField()


class ServiceEntry(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    unit = serializers.CharField()
    price = serializers.CharField()


class ServiceCatalogResponse(serializers.Serializer):
    category = serializers.CharField()
    services = ServiceEntry(many=True)


class AdvertiserRequestResponse(serializers.Serializer):
    request_id = serializers.IntegerField()
    advertiser = serializers.CharField()
    submitted_at = serializers.DateTimeField()
    contract_number = serializers.CharField()
    signed_at = serializers.DateField()


class EmployeeWorkloadResponse(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee = serializers.CharField()
    request_count = serializers.IntegerField()


class QuarterWork(serializers.Serializer):
    work_id = serializers.IntegerField()
    service = serializers.CharField()
    cost = serializers.CharField()


class QuarterEmployee(serializers.Serializer):
    employee_id = serializers.IntegerField()
    employee = serializers.CharField()
    requests = serializers.IntegerField()
    amount = serializers.CharField()
    works = QuarterWork(many=True)


class QuarterlyResponse(serializers.Serializer):
    year = serializers.IntegerField()
    quarter = serializers.IntegerField()
    start_date = serializers.DateField()
    end_exclusive = serializers.DateField()
    employees = QuarterEmployee(many=True)
    total = serializers.CharField()
