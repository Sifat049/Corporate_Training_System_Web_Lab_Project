"""
Django settings - project-er shob configuration ekhane thake.

Banglish note:
- BASE_DIR = backend/ folder er path.
- FRONTEND_DIR = frontend/ folder (HTML templates + CSS + JS ekhane thake).
  Django ke bole dite hoy template ar static file kothay ache - seta niche kora hoyeche.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent          # .../50_Percent_Version/backend
PROJECT_DIR = BASE_DIR.parent                              # .../50_Percent_Version
FRONTEND_DIR = PROJECT_DIR / "frontend"                    # .../50_Percent_Version/frontend

# Academic demo project - production e deploy korle ei key bodle felben
# Banglish: local e kichu set korte hobe na. Live (PythonAnywhere) e environment variable diye bodlano jay.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-corporate-training-demo-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver", ".pythonanywhere.com"]
ALLOWED_HOSTS += [h for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",") if h]
CSRF_TRUSTED_ORIGINS = ["https://*.pythonanywhere.com"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Amader nijer app gulo
    "accounts",   # login, register, role, profile
    "training",   # category, module, assignment, task, feedback, quiz, certificate, comments
    "core",       # notification, audit log, reports, calendar, protected files
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",            # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Template gulo frontend/templates folder e rakha hoyeche
        "DIRS": [FRONTEND_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Sidebar menu role onujayi toiri kore (accounts/context_processors.py)
                "accounts.context_processors.navigation",
                "core.context_processors.extras",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Amra Django-r default User er bodole nijer User model use korchi (role field ache)
AUTH_USER_MODEL = "accounts.User"

# 100% version: password er kono rule nai (8 character, common password, numeric - shob bad).
# Je kono (faka na) password cholbe. Tai validators list ta khali.
AUTH_PASSWORD_VALIDATORS = []

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JS, images) frontend/static folder theke ashe
STATIC_URL = "static/"
STATICFILES_DIRS = [FRONTEND_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"  # collectstatic ekhane file jomay (live server er jonno)

# User upload kora file (video, document, submission) backend/media te jabe
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
MAX_UPLOAD_MB = 50

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Message tag gulo CSS class er sathe match korano
from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {
    message_constants.DEBUG: "info",
    message_constants.INFO: "info",
    message_constants.SUCCESS: "success",
    message_constants.WARNING: "warning",
    message_constants.ERROR: "error",
}

# ---- 100% version extra settings ----
# Password reset email: real SMTP chara demo te email Terminal (console) e print hoy
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "Corporate Training <no-reply@corporate-training.local>"
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # reset link 24 ghonta valid
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # CSV import/form data limit (file upload alada)
