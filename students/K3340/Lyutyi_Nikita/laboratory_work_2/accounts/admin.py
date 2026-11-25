from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административный интерфейс расширенного пользователя."""

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            "Дополнительные данные",
            {
                "fields": (
                    "passport_number",
                    "home_address",
                    "nationality",
                )
            },
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            "Дополнительные данные",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "passport_number",
                    "home_address",
                    "nationality",
                )
            },
        ),
    )

    list_display = (
        "username",
        "first_name",
        "last_name",
        "nationality",
        "is_staff",
    )

    search_fields = (
        "username",
        "first_name",
        "last_name",
    )