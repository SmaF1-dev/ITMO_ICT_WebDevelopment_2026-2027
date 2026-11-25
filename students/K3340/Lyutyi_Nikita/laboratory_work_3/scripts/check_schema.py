"""Запуск: python manage.py shell -c "exec(open('scripts/check_schema.py', encoding='utf-8').read())" (из папки ЛР3)."""
from django.db import connection

expected = {
    "advertiser": ["advertiser_id"],
    "employee": ["employee_id"],
    "service_category": ["category_id"],
    "advertising_service": ["service_id"],
    "material": ["material_id"],
    "material_usage_norm": ["service_id", "material_id"],
    "advertising_request": ["request_id"],
    "request_work": ["work_id"],
    "contract": ["contract_id"],
    "payment_order": ["payment_order_id"],
}
with connection.cursor() as cursor:
    for table, columns in expected.items():
        constraints = connection.introspection.get_constraints(cursor, table)
        primary_keys = [v["columns"] for v in constraints.values() if v["primary_key"]]
        assert len(primary_keys) == 1 and set(primary_keys[0]) == set(columns), (table, primary_keys, columns)
        print("PASS", table, "+".join(columns))
print("Все 10 таблиц и первичные ключи соответствуют согласованной ER-схеме.")
