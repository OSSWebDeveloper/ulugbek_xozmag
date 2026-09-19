"""Ulug'bek Xozmag - Django sozlamalari."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# O'rnatuvchi orqali yig'ilgan dastur («muqim» rejim). Dastur fayllari faqat
# o'qish uchun ochiq papkada turishi mumkin, shuning uchun baza va maxfiy
# kalit foydalanuvchining o'z papkasiga yoziladi.
MUQIM = bool(getattr(sys, "frozen", False))
if MUQIM:
    BASE_DIR = Path(sys._MEIPASS)
    MALUMOT_DIR = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "UlugbekXozmag"
    MALUMOT_DIR.mkdir(parents=True, exist_ok=True)
else:
    MALUMOT_DIR = BASE_DIR

# Maxfiy kalit kodda turmaydi (ombor ochiq). Tartib:
#   1) `XOZMAG_SECRET_KEY` muhit o'zgaruvchisi bo'lsa — o'sha;
#   2) bo'lmasa `.secret_key` fayli (git'ga tushmaydi) — birinchi ishga
#      tushirishda o'zi yasaladi va shu kompyuterda qoladi.
SECRET_KEY = os.environ.get("XOZMAG_SECRET_KEY", "").strip()
if not SECRET_KEY:
    _kalit_fayl = MALUMOT_DIR / ".secret_key"
    if _kalit_fayl.exists():
        SECRET_KEY = _kalit_fayl.read_text(encoding="utf-8").strip()
    else:
        from django.core.management.utils import get_random_secret_key

        SECRET_KEY = get_random_secret_key()
        _kalit_fayl.write_text(SECRET_KEY, encoding="utf-8")
# O'rnatilgan dasturda xatolik sahifalari ko'rsatilmaydi (DEBUG = False),
# ishlab chiqishda esa avvalgidek yoniq turadi.
DEBUG = not MUQIM
ALLOWED_HOSTS = ["*"]

# ngrok orqali tashqaridan kirilganda POST so'rovlar (kirish, saqlash) CSRF
# tekshiruvidan o'tishi uchun ngrok domenlari ishonchli deb belgilanadi.
CSRF_TRUSTED_ORIGINS = [
    "https://*.ngrok-free.app",
    "https://*.ngrok-free.dev",
    "https://*.ngrok.app",
    "https://*.ngrok.io",
]

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
    # Barcha sahifa login talab qiladi (kirish sahifasidan tashqari)
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
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
        "NAME": MALUMOT_DIR / "db.sqlite3",
    }
}

# Testlarda parol xeshlash vaqtni yeydi (har bir testda xodim yaratiladi).
# Faqat `manage.py test` da tez xeshga o'tamiz — ishlashga ta'sir qilmaydi.
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

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

# Kirish / chiqish
LOGIN_URL = "kirish"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "kirish"
# Brauzer yopilguncha seans saqlanadi; 12 soatdan keyin baribir tugaydi
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True

# Pul birligi belgisi (shablonlarda ishlatiladi)
PUL_BIRLIGI = "so'm"

# Dastur versiyasi — yagona manba `versiya.txt` fayli. Uni qo'lda tahrirlash
# shart emas: `python versiya.py 1.1.0 "izoh"` yangilaydi, VERSIYALAR.md ga
# yozadi, commit qiladi va teg qo'yadi.
VERSIYA_FAYL = BASE_DIR / "versiya.txt"
VERSIYA = (VERSIYA_FAYL.read_text(encoding="utf-8").strip()
           if VERSIYA_FAYL.exists() else "0.0.0")
