import os
import sys
from pathlib import Path

import dj_database_url

from .base import *


INSTALLED_APPS += ['whitenoise.runserver_nostatic']

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-local-development-key',
)

DEBUG = env_bool('DJANGO_DEBUG', True)

ALLOWED_HOSTS = env_list(
    'DJANGO_ALLOWED_HOSTS',
    ['127.0.0.1', 'localhost', 'testserver'],
)

CSRF_TRUSTED_ORIGINS = env_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    ['http://127.0.0.1:8000', 'http://localhost:8000'],
)

default_sqlite_url = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
running_tests = len(sys.argv) > 1 and sys.argv[1] == 'test'

if running_tests:
    database_url = os.environ.get('TEST_DATABASE_URL', default_sqlite_url)
else:
    database_url = os.environ.get('DATABASE_URL', default_sqlite_url)

DATABASES = {
    'default': dj_database_url.parse(
        database_url,
        conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        ssl_require=env_bool('DB_SSL_REQUIRE', False),
    )
}

MEDIA_ROOT = Path(
    os.environ.get('DJANGO_MEDIA_ROOT', str(BASE_DIR / 'public' / 'media'))
)

STORAGES['staticfiles'] = {
    'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
}