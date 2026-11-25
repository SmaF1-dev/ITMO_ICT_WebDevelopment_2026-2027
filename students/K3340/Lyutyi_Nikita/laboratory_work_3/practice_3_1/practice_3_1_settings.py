from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = "local-only-orm-practice"
DEBUG = True
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "cars_practice"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "practice.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
