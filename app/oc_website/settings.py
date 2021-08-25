import os
from pathlib import Path


def get_setting(name: str) -> str:
    ret = os.environ.get(name)
    if not ret:
        raise RuntimeError(f"Missing configuration variable {name}")
    return ret


BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent

# persistent directory with animu data
DATA_DIR = REPO_DIR / "data"

# persistent directory with generated .torrent files
TORRENTS_DIR = REPO_DIR / "torrents"

# persistent directory where to put .torrent files for transmission to add
# (transmission renames added .torrent files to .torrent.added at arbitrary
# points in time, which causes races with the .torrent upload code, hence this
# cannot be the same directory as TORRENTS_DIR and is used as a "fire and
# forget" mechanism)
TRANSMISSION_WATCHDIR = REPO_DIR / "transmission-watchdir"

SECRET_KEY = get_setting("SECRET_KEY")
DEBUG = os.environ.get("DEBUG", "False").lower() in {"1", "true"}
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "oc_website",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "oc_website.middleware.TimezoneMiddleware",
]

ROOT_URLCONF = "oc_website.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "oc_website.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/uploads/"
MEDIA_ROOT = BASE_DIR / "uploads"

CELERY_BROKER_URL = "redis://redis:6379"
CELERY_RESULT_BACKEND = "redis://redis:6379"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_IMPORTS = ("oc_website.tasks",)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ANIDEX_API_URL = "https://anidex.info/api/"
ANIDEX_API_KEY = get_setting("ANIDEX_API_KEY")
ANIDEX_GROUP_ID = get_setting("ANIDEX_GROUP_ID")
ANIDEX_CATEGORY_ID = 1
ANIDEX_LANGUAGE_ID = 1
ANIDEX_MAX_RETRIES = 3

NYAA_SI_API_URL = "https://nyaa.si/api/upload"
NYAA_SI_USER = get_setting("NYAA_SI_USER")
NYAA_SI_PASS = get_setting("NYAA_SI_PASS")
NYAA_SI_INFO = "https://oldcastle.moe"
NYAA_SI_CATEGORY_ID = "1_2"

NYAA_PANTSU_API_URL = "https://nyaa.net/api/upload"
NYAA_PANTSU_USER = get_setting("NYAA_PANTSU_USER")
NYAA_PANTSU_PASS = get_setting("NYAA_PANTSU_PASS")
NYAA_PANTSU_API_KEY = get_setting("NYAA_PANTSU_API_KEY")
NYAA_PANTSU_WEBSITE = "https://oldcastle.moe"
NYAA_PANTSU_CATEGORY_ID = "3_5"
NYAA_PANTSU_LANGUAGES = "en"

TORRENT_TRACKERS = [
    "http://anidex.moe:6969/announce",
    "http://nyaa.tracker.wf:7777/announce",
    "udp://tracker.uw0.xyz:6969",
]
TORRENT_MAX_PIECE_SIZE = 4 * 1024 * 1024

FILE_UPLOAD_PERMISSIONS = 0o644
