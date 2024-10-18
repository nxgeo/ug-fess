from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent

INSTALLED_APPS = ["db"]

DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600, conn_health_checks=True, ssl_require=True
    )
}

TIME_ZONE = "Asia/Jakarta"

DEFAULT_AUTO_FIELD = "django.db.models.SmallAutoField"
