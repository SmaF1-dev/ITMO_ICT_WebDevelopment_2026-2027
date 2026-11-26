from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = "local-practice-only-do-not-deploy"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "warriors",
]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]
ROOT_URLCONF = "practice_urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
    ]},
}]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "practice.sqlite3"}}
STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
                  "DEFAULT_PAGINATION_CLASS": None}
