
from django.templatetags.static import static
from django.urls import reverse
from django.utils import timezone
from jinja2 import Environment


def url(name, **kwargs):
    """Создаёт URL по имени маршрута Django."""
    return reverse(name, kwargs=kwargs or None)


def datetime_local(value):
    """Форматирует время в часовом поясе проекта."""
    if value is None:
        return "—"

    if timezone.is_aware(value):
        value = timezone.localtime(value)

    return value.strftime("%d.%m.%Y %H:%M")


def environment(**options):
    """Создаёт и настраивает окружение Jinja2."""
    env = Environment(**options)

    env.globals.update({
        "url": url,
        "static": static,
        "datetime_local": datetime_local,
    })

    return env
