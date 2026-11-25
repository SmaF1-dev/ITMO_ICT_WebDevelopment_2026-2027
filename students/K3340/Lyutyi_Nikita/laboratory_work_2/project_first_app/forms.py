from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Car, CarOwner


User = get_user_model()


class CarOwnerForm(forms.ModelForm):
    """Форма создания владельца автомобиля."""

    class Meta:
        model = CarOwner

        fields = [
            "first_name",
            "last_name",
            "birth_date",
        ]

        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "birth_date": "Дата рождения",
        }

        widgets = {
            "birth_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date"},
            ),
        }


class CarForm(forms.ModelForm):
    """Форма создания и редактирования автомобиля."""

    class Meta:
        model = Car

        fields = [
            "brand",
            "model",
            "color",
            "registration_number",
        ]

        labels = {
            "brand": "Марка",
            "model": "Модель",
            "color": "Цвет",
            "registration_number": "Регистрационный номер",
        }


class OwnerUserCreationForm(UserCreationForm):
    """Создание учётной записи вместе с профилем владельца."""

    birth_date = forms.DateField(
        label="Дата рождения",
        required=False,
        widget=forms.DateInput(
            format="%Y-%m-%d",
            attrs={"type": "date"},
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "passport_number",
            "home_address",
            "nationality",
        )

        labels = {
            "username": "Логин",
            "first_name": "Имя",
            "last_name": "Фамилия",
        }

    field_order = (
        "username",
        "first_name",
        "last_name",
        "birth_date",
        "passport_number",
        "home_address",
        "nationality",
        "password1",
        "password2",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        required_fields = (
            "first_name",
            "last_name",
            "passport_number",
            "home_address",
            "nationality",
        )

        for field_name in required_fields:
            self.fields[field_name].required = True