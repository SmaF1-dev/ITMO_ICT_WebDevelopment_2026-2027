import re

from django import forms
from django.core.exceptions import ValidationError


class CheckInForm(forms.Form):
    """Форма назначения номера билета сотрудником."""

    ticket_number = forms.CharField(
        label="Номер билета",
        min_length=6,
        max_length=40,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "placeholder": "DEMO-TKT-0002",
                "autocomplete": "off",
            }
        ),
    )

    def clean_ticket_number(self):
        number = self.cleaned_data["ticket_number"].upper()

        if not re.fullmatch(r"[A-Z0-9-]+", number):
            raise ValidationError(
                "Используйте латинские буквы, цифры и дефисы."
            )

        return number