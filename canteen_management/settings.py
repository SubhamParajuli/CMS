import os


DJANGO_ENV = os.environ.get('DJANGO_ENV', 'local').strip().lower()

if DJANGO_ENV in {'production', 'prod', 'railway'}:
    from .production import *  # noqa: F401,F403
elif DJANGO_ENV in {'local', 'development', 'dev'}:
    from .local import *  # noqa: F401,F403
else:
    raise RuntimeError(
        "Unsupported DJANGO_ENV value. Use 'local' or 'production'."
    )
