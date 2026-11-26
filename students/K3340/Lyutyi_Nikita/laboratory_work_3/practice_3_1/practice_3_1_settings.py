from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = "local-only-orm-practice"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "cars_practice"]
ROOT_URLCONF = "practice_3_1_urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "practice.sqlite3"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
