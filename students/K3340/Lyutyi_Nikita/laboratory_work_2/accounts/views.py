from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import PublicRegistrationForm


def register(request):
    """Регистрация обычного пользователя."""

    if request.user.is_authenticated:
        return redirect("project_first_app:car_list")

    if request.method == "POST":
        form = PublicRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect(
                "project_first_app:car_list"
            )

    else:
        form = PublicRegistrationForm()

    return render(
        request,
        "accounts/register.html",
        {"form": form},
    )


@require_POST
def logout_view(request):
    """Завершение пользовательской сессии."""

    logout(request)

    return redirect("accounts:login")