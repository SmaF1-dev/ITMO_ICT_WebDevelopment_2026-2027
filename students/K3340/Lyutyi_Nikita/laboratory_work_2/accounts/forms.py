from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm


User = get_user_model()


class PublicRegistrationForm(UserCreationForm):
    """Форма самостоятельной регистрации пользователя."""

    email = forms.EmailField(
        label="Электронная почта",
        required=True,
    )

    class Meta(UserCreationForm.Meta):
        model = User

        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
        )

        labels = {
            "username": "Логин",
            "first_name": "Имя",
            "last_name": "Фамилия",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["first_name"].required = True
        self.fields["last_name"].required = True