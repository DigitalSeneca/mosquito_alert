from django.utils.translation import ugettext_lazy as _
import tigaserver_project as project_module
import django.conf.global_settings as DEFAULT_SETTINGS
import pytz
from datetime import datetime

"""
Django settings for tigaserver_project project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


PROJECT_DIR = os.path.dirname(os.path.realpath(project_module.__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

SECRET_KEY = 'h0v(25z3u9yquh+01+#%tj@7iyk*raq!-6)jwz+0ac^h2grd0@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = []

# Application definition


#TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
#    'django.core.context_processors.request',
#)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'rest_framework.authtoken',
    'tigaserver_app',
    'tigamap',
    'tigahelp',
    'tigacrafting',
    'tigapublic',
    'rest_framework',
    'leaflet',
    'stats',
    'floppyforms',
    'taggit',
    'django_messages',
    'tigaserver_messages',
    'tigascoring',
    'django.contrib.sites',
    'django_filters',
)

'''
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
'''
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'tigaserver_project.urls'

WSGI_APPLICATION = 'tigaserver_project.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = True

LANGUAGES = (
    ('es', _('Spanish')),
    ('ca', _('Catalan')),
    ('en', _('English')),
    ('zh-cn', _('Chinese')),
)

LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = ''

# STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

MEDIA_URL = '/media/'

MEDIA_ROOT = ''

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend',]
}

LEAFLET_CONFIG = {
    'DEFAULT_CENTER': (40.0, -4.0),
    'DEFAULT_ZOOM': 6,
    'MINIMAP': True,
    'PLUGINS': {
        'marker_cluster_yellow': {
            'css': ['tigamap/MarkerCluster.css', 'tigamap/MarkerCluster.tigamap_yellow.css'],
            'js': 'tigamap/leaflet.markercluster.js',
        },
        'marker_cluster_yellow_single': {
            'css': ['tigamap/MarkerCluster.css', 'tigamap/MarkerCluster.tigamap_yellow_single.css'],
            'js': 'tigamap/leaflet.markercluster.js',
        },
        'marker_cluster_blue': {
            'css': ['tigamap/MarkerCluster.css', 'tigamap/MarkerCluster.tigamap_blue.css'],
            'js': 'tigamap/leaflet.markercluster.js',
        },
        'marker_cluster_blue_yellow': {
            'css': ['tigamap/MarkerCluster.css', 'tigamap/MarkerCluster.tigamap_blue_yellow.css'],
            'js': 'tigamap/leaflet.markercluster.js',
        },
        'oms': {
            'css': [],
            'js': 'tigamap/oms.min.js',
            'auto-include': True,
        }
    }
}

#TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

# This is the cuttoff score above which a photo will be considered "crowd-validated"
CROWD_VALIDATION_CUTOFF = 0

START_TIME = pytz.utc.localize(datetime(2014, 6, 13))

IOS_START_TIME = pytz.utc.localize(datetime(2014, 6, 24))

SOUTH_MIGRATION_MODULES = {
    'taggit': 'taggit.south_migrations',
    'django_messages': 'django_messages.south_migrations',
}

USERS_IN_STATS = [16, 33, 18, 17, 31, 32, 35, 34]

#PUSH KILL SWITCHES
DISABLE_PUSH_IOS = False
DISABLE_PUSH_ANDROID = False

# CELERY STUFF
BROKER_URL = 'redis://localhost:6379'
CELERY_RESULT_BACKEND = 'redis://localhost:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
#every 15 minutes
CELERY_REFRESH_SCORE_FREQUENCY = '*/15'

APNS_ADDRESS = 'gateway.push.apple.com'
#APNS_ADDRESS = 'gateway.sandbox.push.apple.com'
FCM_ADDRESS = 'https://fcm.googleapis.com/fcm/send'

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240
SITE_ID = 1
from tigaserver_project.settings_local import *
