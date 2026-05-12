"""
Django settings for config project.
"""

import os
from pathlib import Path

# settings.py (or base.py / dev.py / prod.py depending on your setup)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-fvyg4s259i8yf8+g)bsj!v)r_--bnq$8@+5v63*1u&*f)@9x(!'

ALLOWED_HOSTS = ["*"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "http")

CSRF_TRUSTED_ORIGINS = [
    'http://192.168.1.18',
    'http://172.20.10.250',
    'http://172.20.208.155',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crueremisiones',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
				"django.template.context_processors.csrf",
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

import os

DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': os.getenv('DB_DEFAULT_NAME', 'GestorInstitucional'),
        'USER': os.getenv('DB_DEFAULT_USER', 'apantoja'),
        'PASSWORD': os.getenv('DB_DEFAULT_PASSWORD', 'ConsultasPantojaHUDN_2026$'),
        'HOST': os.getenv('DB_DEFAULT_HOST', '172.20.100.209'),
        'PORT': os.getenv('DB_DEFAULT_PORT', ''),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
            'timeout': 30,
        },
    },
}

# No database router needed — single database (institutional MSSQL)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internacionalización ────────────────────────────────────────────────────
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = False

# ─── Configuration for running either: local or service  ─────────────────────────
DEBUG = True
LOCAL = False  # Run as python manage.py runserver instead as a service

USE_X_FORWARDED_HOST = True
STATICFILES_DIRS  = []
if LOCAL:
	# ─── Archivos estáticos ──────────────────────────────────────────────────────
	FORCE_SCRIPT_NAME = '/'
	STATIC_URL        = '/static/'
	STATIC_ROOT       = BASE_DIR / 'staticfiles'
	# ─── Archivos de medios ──────────────────────────────────────────────────────
	MEDIA_URL        = '/media/'
	MEDIA_ROOT = BASE_DIR / 'media'
	# ─── Autenticación ───────────────────────────────────────────────────────────
	LOGIN_URL = '/login/'
	LOGIN_REDIRECT_URL = '/'
	LOGOUT_REDIRECT_URL = '/login/'
else:
	# ─── Archivos estáticos ──────────────────────────────────────────────────────
	FORCE_SCRIPT_NAME = '/crue-remisiones'
	STATIC_URL        = '/crue-remisiones/static/'
	STATIC_ROOT       = BASE_DIR / 'staticfiles'
	# ─── Archivos de medios ──────────────────────────────────────────────────────
	MEDIA_URL        = '/crue-remisiones/media/'
	MEDIA_ROOT = BASE_DIR / 'media'
	# ─── Autenticación ───────────────────────────────────────────────────────────
	LOGIN_URL = '/crue-remisiones/login/'
	LOGIN_REDIRECT_URL = '/crue-remisiones/'
	LOGOUT_REDIRECT_URL = '/crue-remisiones/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de usuario: se usa el del proyecto padre (django.contrib.auth.models.User por defecto)
# AUTH_USER_MODEL no se define aquí — el proyecto padre lo controla.

# Email (configurar SMTP en producción)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'noreply@hudn.gov.co'
