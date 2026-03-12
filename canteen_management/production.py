import os
from pathlib import Path

import dj_database_url

from .base import *


SECRET_KEY = env_required('DJANGO_SECRET_KEY')
DEBUG = False

railway_public_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '').strip()

default_allowed_hosts = [host for host in [railway_public_domain, '.railway.app'] if host]

ALLOWED_HOSTS = env_list(
    'DJANGO_ALLOWED_HOSTS',
    default_allowed_hosts,
)

default_csrf_origins = []
if railway_public_domain:
    default_csrf_origins.append(f'https://{railway_public_domain}')

CSRF_TRUSTED_ORIGINS = env_list(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default_csrf_origins,
)

DATABASES = {
    'default': dj_database_url.parse(
        env_required('DATABASE_URL'),
        conn_max_age=int(os.environ.get('DB_CONN_MAX_AGE', '600')),
        ssl_require=env_bool('DB_SSL_REQUIRE', True),
    )
}

MEDIA_URL = os.environ.get('DJANGO_MEDIA_URL', '/media/')
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', '/app/media'))

STORAGES['staticfiles'] = {
    'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
}

SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    'DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS',
    True,
)
SECURE_HSTS_PRELOAD = env_bool('DJANGO_SECURE_HSTS_PRELOAD', True)