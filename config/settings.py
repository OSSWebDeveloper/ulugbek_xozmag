"""Ulug'bek Xozmag - Django sozlamalari."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Maxfiy kalit kodda turmaydi (ombor ochiq). Tartib:
#   1) `XOZMAG_SECRET_KEY` muhit o'zgaruvchisi bo'lsa — o'sha;
#   2) bo'lmasa `.secret_key` fayli (git'ga tushmaydi) — birinchi ishga
#      tushirishda o'zi yasaladi va shu kompyuterda qoladi.
SECRET_KEY = os.environ.get("XOZMAG_SECRET_KEY", "").strip()
if not SECRET_KEY:
    _kalit_fayl = BASE_DIR / ".secret_key"
    if _kalit_fayl.exists():
        SECRET_KEY = _kalit_fayl.read_text(encoding="utf-8").strip()
    else:
        from django.core.management.utils import get_random_secret_key

        SECRET_KEY = get_random_secret_key()
        _kalit_fayl.write_text(SECRET_KEY, encoding="utf-8")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ombor",
    "qarz",
    "sotuv",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# Django 6 dan boshlab shablonlar DEBUG rejimida ham keshlanadi. Ishlab
# chiqishda bu xalaqit beradi: shablon o'zgarsa sayt qayta ishga
# tushirilmaguncha eski holat ko'rinaveradi.
_YUKLAGICHLAR = [
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "loaders": (
                _YUKLAGICHLAR if DEBUG
                else [("django.template.loaders.cached.Loader", _YUKLAGICHLAR)]
            ),
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.kontekst.versiya",
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

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Pul birligi belgisi (shablonlarda ishlatiladi)
PUL_BIRLIGI = "so'm"

# Dastur versiyasi — yagona manba `versiya.txt` fayli. Uni qo'lda tahrirlash
# shart emas: `python versiya.py 1.1.0 "izoh"` yangilaydi, VERSIYALAR.md ga
# yozadi, commit qiladi va teg qo'yadi.
VERSIYA_FAYL = BASE_DIR / "versiya.txt"
VERSIYA = (VERSIYA_FAYL.read_text(encoding="utf-8").strip()
           if VERSIYA_FAYL.exists() else "0.0.0")
