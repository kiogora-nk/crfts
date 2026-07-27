from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-crfts-2026-secure-file-tracking-system'
DEBUG = True
ALLOWED_HOSTS = ['*']
INSTALLED_APPS = [
    'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes',
    'django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles',
    'rest_framework','corsheaders',
    'apps.accounts','apps.departments','apps.registry','apps.transfers',
    'apps.reports','apps.notifications','apps.audit','apps.ai_engine',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware','django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'crfts.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'crfts.wsgi.application'
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3'}}
AUTH_USER_MODEL = 'accounts.User'
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR/'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR/'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/login/'
SESSION_COOKIE_AGE = 900
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400
