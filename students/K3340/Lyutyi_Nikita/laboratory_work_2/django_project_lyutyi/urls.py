
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView


urlpatterns = [
    path(
        "",
        RedirectView.as_view(
            pattern_name="flights:flight_list",
            permanent=False,
        ),
        name="home",
    ),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("flights/", include("flights.urls")),
    path("", include("project_first_app.urls")),
]
