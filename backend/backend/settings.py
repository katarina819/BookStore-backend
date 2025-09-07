import os
from pathlib import Path

# Osnovni direktorij projekta
BASE_DIR = Path(__file__).resolve().parent.parent

# Sigurnost
SECRET_KEY = 'zr9&f55!tg^zvq2)3n#1s^i14myb32odpd&_tw0adj@q+!=m_3'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Aplikacije
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'requests_app',  # tvoja app
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',   # 👈 ovo ide odmah iza SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


CORS_ALLOWED_ORIGINS = [
    "http://localhost:20281",  # Angular frontend
]

ROOT_URLCONF = 'backend.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Baza podataka (koristi SQLite za lokalno testiranje)
# Baza podataka (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bookstay',          # ime tvoje baze
        'USER': 'postgres',     # korisnik baze
        'PASSWORD': '1234',  # lozinka korisnika
        'HOST': 'localhost',          # ili IP servera baze
        'PORT': '5432',               # default port PostgreSQL
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internacionalizacija
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Europe/Zagreb'
USE_I18N = True
USE_TZ = True

# Staticki fajlovi
STATIC_URL = '/static/'

# Django REST Framework + JWT
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
