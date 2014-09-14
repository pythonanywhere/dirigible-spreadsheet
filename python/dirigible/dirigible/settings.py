# Django settings for dirigible project.

import os
import sys


# Debug settings, overridden on dev machines.
DEBUG = True
ADMIN_EMAIL = ''
FEEDBACK_EMAIL = ''
try:
    from development_settings import *
except ImportError:
    pass

TEMPLATE_DEBUG = DEBUG


DEFAULT_FROM_EMAIL = ''
SERVER_EMAIL = DEFAULT_FROM_EMAIL
ADMINS = (
    ('Dirigible Admin', ADMIN_EMAIL),
)
MANAGERS = ADMINS


# DB settings, overridden on a per-machine basis.
DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'dirigible.db'
DATABASE_USER = ''
DATABASE_PORT = ''

# Email server settings.
EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = True


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'secretsecretsecret'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'dirigible.urls'

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'registration',
    'featured_sheet',
    'feedback',
    'info_pages',
    'shared',
    'sheet',
    'user',
)

ACCOUNT_ACTIVATION_DAYS = 14

# The URL for the login page
LOGIN_URL = '/login'

# The place where people are sent after logging in if they came to the login
# page directly
LOGIN_REDIRECT_URL = '/'

