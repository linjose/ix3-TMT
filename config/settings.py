from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def load_local_env(path: Path) -> None:
    """Load simple KEY=value lines for native installs; real environment wins."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if value and value[0:1] == value[-1:] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_local_env(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, "1" if default else "0").strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = env_bool("DJANGO_DEBUG", True)
if not DEBUG and (SECRET_KEY == "dev-only-change-me" or SECRET_KEY.startswith("change-me")):
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Set a strong DJANGO_SECRET_KEY before running with DJANGO_DEBUG=0")
ALLOWED_HOSTS = [x.strip() for x in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if x.strip()]
for _local_host in ("127.0.0.1", "localhost"):
    if _local_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_local_host)
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tmt",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "tmt.context_processors.tmt_settings",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

if os.getenv("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "tmt"),
            "USER": os.getenv("DB_USER", "tmt"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hant"
TIME_ZONE = os.getenv("TZ", "Asia/Taipei")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
MEDIA_ROOT = Path(os.getenv("TMT_MEDIA_ROOT", str(BASE_DIR / "media")))
MEDIA_URL = "/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "tmt:home"
LOGOUT_REDIRECT_URL = "login"

# TMT runtime settings
TMT_MAX_UPLOAD_MB = env_int("TMT_MAX_UPLOAD_MB", 100)
TMT_ALLOWED_EXTENSIONS = tuple(x.strip().lower() for x in os.getenv("TMT_ALLOWED_EXTENSIONS", ".pptx,.ppt").split(",") if x.strip())
TMT_OCR_ENABLED = env_bool("TMT_OCR_ENABLED", True)
TMT_OCR_LANGUAGES = os.getenv("TMT_OCR_LANGUAGES", "chi_tra+eng")
TMT_OCR_TRIGGER_TEXT_LENGTH = env_int("TMT_OCR_TRIGGER_TEXT_LENGTH", 50)
TMT_OCR_VISUAL_TRIGGER_TEXT_LENGTH = env_int("TMT_OCR_VISUAL_TRIGGER_TEXT_LENGTH", 250)
TMT_RENDER_DPI = env_int("TMT_RENDER_DPI", 160)
TMT_THUMBNAIL_WIDTH = env_int("TMT_THUMBNAIL_WIDTH", 640)
TMT_OCR_TIMEOUT_SECONDS = env_int("TMT_OCR_TIMEOUT_SECONDS", 120)
TMT_OCR_PSM = env_int("TMT_OCR_PSM", 11)
TMT_JOB_POLL_SECONDS = env_int("TMT_JOB_POLL_SECONDS", 10)
TMT_MAX_AUTO_TAGS = env_int("TMT_MAX_AUTO_TAGS", 8)
TMT_ALLOW_SELF_SIGNUP = env_bool("TMT_ALLOW_SELF_SIGNUP", False)
TMT_OCR_WORKERS = max(1, env_int("TMT_OCR_WORKERS", 1))

# Sensible production defaults; HTTPS termination can be added at Nginx.
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
