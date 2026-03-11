#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${DATABASE_URL:-}" ]]; then
  echo "Waiting for database to be ready..."
  python - <<'PY'
import os
import time
import psycopg

db_url = os.environ.get("DATABASE_URL")
timeout = int(os.environ.get("DJANGO_DB_WAIT_TIMEOUT", "60"))
start = time.time()

while True:
    try:
        conn = psycopg.connect(db_url, connect_timeout=5)
        conn.close()
        print("Database is ready.")
        break
    except Exception as exc:
        if time.time() - start > timeout:
            raise
        time.sleep(2)
PY
fi

python manage.py migrate --noinput

if [[ -n "${DJANGO_FIXTURE_PATH:-}" && -f "${DJANGO_FIXTURE_PATH}" ]]; then
  python manage.py shell <<'PY'
import os
from django.core.management import call_command
from django.contrib.auth import get_user_model
from inventory.models import Inventory

fixture_path = os.environ.get("DJANGO_FIXTURE_PATH")
force = os.environ.get("DJANGO_FIXTURE_FORCE", "").lower() in {"1", "true", "yes"}

User = get_user_model()
has_users = User.objects.exists()
has_inventory = Inventory.objects.exists()

if force or not (has_users or has_inventory):
    call_command("loaddata", fixture_path, verbosity=1)
    print("Loaded fixture:", fixture_path)
else:
    print("Skipping fixture load; data already present.")
PY
fi

python manage.py collectstatic --noinput

if [[ -n "${DJANGO_ADMIN_USERNAME:-}" && -n "${DJANGO_ADMIN_PASSWORD:-}" && -n "${DJANGO_ADMIN_USER_CODE:-}" ]]; then
  python manage.py shell <<'PY'
import os
from django.contrib.auth import get_user_model

username = os.environ.get("DJANGO_ADMIN_USERNAME")
password = os.environ.get("DJANGO_ADMIN_PASSWORD")
user_code = os.environ.get("DJANGO_ADMIN_USER_CODE")
email = os.environ.get("DJANGO_ADMIN_EMAIL", "") or ""
reset = os.environ.get("DJANGO_ADMIN_RESET_PASSWORD", "").lower() in {"1", "true", "yes"}

User = get_user_model()
user = User.objects.filter(username=username).first()
if user is None:
    User.objects.create_superuser(
        username=username,
        password=password,
        email=email,
        user_code=user_code,
        role="admin",
    )
    print("Created admin user:", username)
elif reset:
    user.set_password(password)
    user.save(update_fields=["password"])
    print("Reset admin password for:", username)
else:
    print("Admin user already exists:", username)
PY
fi

exec gunicorn canteen_management.wsgi:application --access-logfile - --log-file -
