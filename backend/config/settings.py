from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "apps.core",
    "apps.accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": []},
    }
]

DATABASES = {"default": env.db("DATABASE_URL")}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CHROMA_URL = env("CHROMA_URL", default="http://localhost:8001")
NEO4J_URL = env("NEO4J_URL", default="bolt://localhost:7687")
NEO4J_USER = env("NEO4J_USER", default="neo4j")
NEO4J_PASSWORD = env("NEO4J_PASSWORD", default="")

# Backs DRF throttling below. Also what P3's Celery work will use as a broker.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.DeviceTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    # "device-create" is applied explicitly to POST /api/devices/ (see
    # apps.accounts.views), which mints a row per call against the only
    # non-rebuildable datastore and so gets a tighter ceiling than the
    # general anonymous rate.
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",
        "device-create": "10/hour",
        "auth": "20/hour",
        # Read-only account-scoped endpoints (summary, device list/revoke,
        # export). Not credential-checking, so device-keyed is fine; higher
        # than "auth" because a session/devices screen may poll or refresh
        # more than once a minute.
        "account": "120/hour",
    },
}

# Gate for the OpenAPI schema and its browsable UI. A schema enumerates the
# whole API surface, so it is not served publicly: access requires DEBUG, or
# this token in an X-Docs-Token header. Empty (the default) disables the
# token path entirely, so production serves the schema to nobody by default.
DOCS_TOKEN = env("DOCS_TOKEN", default="")

SPECTACULAR_SETTINGS = {
    "TITLE": "Femopedia API",
    "DESCRIPTION": (
        "Anonymous AI health companion. The only credential is a device token: "
        "call POST /api/devices/ once, keep the returned token on the device, "
        "and send it as X-Device-Token on every authenticated request. No "
        "personal identifier is required or accepted."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SORT_OPERATIONS": True,
}

# Keyed separately from SECRET_KEY so that rotating a Django session secret
# does not silently destroy the ability to find or read stored identifiers.
# IDENTIFIER_PEPPER keys the blind index used for lookup; FIELD_ENCRYPTION_KEY
# encrypts the identifier values themselves. Losing either is unrecoverable,
# so both must be backed up somewhere other than the database they protect.
IDENTIFIER_PEPPER = env("IDENTIFIER_PEPPER")
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")

# Console backend in development; a real sending service is a launch
# dependency, since verification mail landing in spam breaks signup for
# anyone whose only route in is an email address.
EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@femopedia.local")
ACCOUNT_VERIFICATION_URL = env(
    "ACCOUNT_VERIFICATION_URL", default="http://localhost:3000/verify-email"
)
ACCOUNT_PASSWORD_RESET_URL = env(
    "ACCOUNT_PASSWORD_RESET_URL", default="http://localhost:3000/reset-password"
)
