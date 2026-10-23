from django import forms

from .models import Car, CarOwner


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