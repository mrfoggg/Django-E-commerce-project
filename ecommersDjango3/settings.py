"""
Django settings for ecommersDjango3 project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '0kgy5_u#6unrbrjm^yb4p367+q28_%qdo1*7k98plq_9_ez((1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.forms',
    'django_summernote',
    'mptt',
    'nested_admin',
    # Простые инструменты для обработки строк на русском языке (выберите правильную форму для множественного числа,
    # словесное представление чисел, дат на русском языке без локали, транслитерации и т. д.)
    'pytils',
    'django_json_widget',
    'pysnooper',
    # 'debug_toolbar',
    'home',
    'products',
    'baton.autodiscover',
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

ROOT_URLCONF = 'ecommersDjango3.urls'
FORM_RENDERER = 'django.forms.renderers.TemplatesSetting'

TEMPLATE_DIR = BASE_DIR / "templates"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'ecommersDjango3.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_db',
        'USER': 'snipadmin',
        'PASSWORD': '7898',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Africa/Mbabane'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # ...
]
X_FRAME_OPTIONS = 'SAMEORIGIN'

ALLOWED_HOSTS = ['*']

BATON = {
    'SITE_HEADER': 'Baton',
    'SITE_TITLE': 'Baton',
    'INDEX_TITLE': 'Site administration',
    'SUPPORT_HREF': 'https://github.com/otto-torino/django-baton/issues',
    'COPYRIGHT': 'copyright © 2017 <a href="https://www.otto.to.it">Otto srl</a>',  # noqa
    'POWERED_BY': '<a href="https://www.otto.to.it">Otto srl</a>',
    'CONFIRM_UNSAVED_CHANGES': True,
    'SHOW_MULTIPART_UPLOADING': True,
    'ENABLE_IMAGES_PREVIEW': True,
    'CHANGELIST_FILTERS_IN_MODAL': True,
    'CHANGELIST_FILTERS_ALWAYS_OPEN': False,
    'MENU_ALWAYS_COLLAPSED': False,
    'MENU_TITLE': 'Menu',
    'GRAVATAR_DEFAULT_IMG': 'retro',
    'MENU': (
        {'type': 'title', 'label': 'Пользователи', 'apps': ('auth',)},
        {
            'type': 'app',
            'name': 'auth',
            'label': 'Учетные записи админки',
            'icon': 'fa fa-lock',
            'models': (
                {
                    'name': 'user',
                    'label': 'Пользователи'
                },
                {
                    'name': 'group',
                    'label': 'Группы пользователей'
                },
            )
        },
        {'type': 'title', 'label': 'Товары', 'apps': ('products',)},
        {'type': 'free', 'label': 'Каталог', 'default_open': True, 'children': [
            {'type': 'model', 'label': 'Список товаров', 'name': 'product', 'app': 'products'},
            {'type': 'model', 'label': 'Категории товаров', 'name': 'category', 'app': 'products'},
            {'type': 'model', 'label': 'Сочетания категорий', 'name': 'categorycollection', 'app': 'products'},
            {'type': 'model', 'label': 'Бренды', 'name': 'brand', 'app': 'products'},
            {'type': 'model', 'label': 'Страны', 'name': 'country', 'app': 'products'},
            {'type': 'model', 'label': 'Фото товаров', 'name': 'productimage', 'app': 'products'},
        ]},
        {'type': 'free', 'label': 'Характеристики', 'default_open': True, 'children': [
            {'type': 'model', 'label': 'Группы атрибутов', 'name': 'attrgroup', 'app': 'products'},
            {'type': 'model', 'label': 'Атрибуты', 'name': 'attribute', 'app': 'products'},
            {'type': 'model', 'label': 'Значения атрибутов', 'name': 'attributevalue', 'app': 'products'},
        ]},
        {'type': 'free', 'label': 'Custom Link', 'url': 'http://www.google.it', 'perms': ('flatpages.add_flatpage',
                                                                                          'auth.change_user')},
        {'type': 'free', 'label': 'My parent voice', 'default_open': True, 'children': [
            {'type': 'free', 'label': 'Another custom link', 'url': 'http://www.google.it'},
        ]},
    ),
    # 'ANALYTICS': {
    #     'CREDENTIALS': os.path.join(BASE_DIR, 'credentials.json'),
    #     'VIEW_ID': '12345678',
    # }
}
