"""
Django settings for smartgame project.

Generated by 'django-admin startproject' using Django 3.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path
from django.contrib.messages import constants as message_constants
from smartgame.secret import get_socialkey, get_socialsecret, get_secretkey

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = 'SmartGame'   # Добавлено Имя приложения

DEFAULT_AUTO_FIELD='django.db.models.AutoField' # Добавлено Автогенерация первичного ключа
DATE_INPUT_FORMATS = ['%d-%m-%Y'] # Добавлено Формат даты


LOGIN_REDIRECT_URL = 'brainstorm:smartgames' # Добавлено

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_secretkey()
#DB_PASS = os.environ.get('DB_POSTGRES_PASS')


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    #Добавленные
    'brainstorm.apps.BrainstormConfig',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'crispy_forms',

    # ... include the providers you want to enable:
    'allauth.socialaccount.providers.vk',

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

ROOT_URLCONF = 'smartgame.urls'

# Social Login Django
#SOCIAL_AUTH_JSONFIELD_ENABLED = True

AUTHENTICATION_BACKENDS = (
    #'social_core.backends.vk.VKOAuth2',          # бекенд авторизации через ВКонтакте
    'django.contrib.auth.backends.ModelBackend', # бекенд классической аутентификации, чтобы работала авторизация через обычный логин и пароль
    'allauth.account.auth_backends.AuthenticationBackend',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR.joinpath("templates"))],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends', # Добавлено
                'social_django.context_processors.login_redirect',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'smartgame.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'ru-RU' #Русский язык

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = False # Выключить таймзону


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = '/static/'
#STATICFILES_DIRS = (
#os.path.join(BASE_DIR, 'static'),
#)

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

CRISPY_TEMPLATE_PACK = 'bootstrap4'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SOCIAL_AUTH_VK_OAUTH2_KEY = get_socialkey()
SOCIAL_AUTH_VK_OAUTH2_SECRET = get_socialsecret()

SITE_ID=2 #Для социальной аутонтификации. Первый сайт тестовый, мой второй
ACCOUNT_EMAIL_VERIFICATION = "none" #не нужно подтверждение через почту
LOGIN_REDIRECT_URL = "brainstorm:smartgames" #cnh
ACCOUNT_LOGOUT_ON_GET = True

#Для всплывающих сообщений
MESSAGE_TAGS = {message_constants.DEBUG: 'debug',
                message_constants.INFO: 'info',
                message_constants.SUCCESS: 'success',
                message_constants.WARNING: 'warning',
                message_constants.ERROR: 'danger',}
