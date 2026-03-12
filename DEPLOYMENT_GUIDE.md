# Railway Deployment Guide

Updated: 2026-03-12

Project root: `/home/suhan/CMS`

This guide is aligned with the current codebase, including:

- split settings in `canteen_management/settings.py`, `base.py`, `local.py`, and `production.py`
- PostgreSQL in production through `dj-database-url`
- WhiteNoise static file serving
- Gunicorn startup from `Procfile`
- persistent media storage mounted at `/app/media`

## 1. Pre-Push Checklist

Before pushing to GitHub, confirm the repository root contains:

- `manage.py`
- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `data-migration.json`

Confirm these are not committed:

- `.env`
- local uploaded media files
- local SQLite-only database files

Run the final local validation commands:

```bash
source myenv/bin/activate
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

## 2. Push the Repository to GitHub

If the repository is not connected yet:

```bash
git init
git branch -M main
git add .
git commit -m "Prepare Railway deployment"
git remote add origin https://github.com/<your-username>/<your-repository>.git
git push -u origin main
```

If the repository already exists:

```bash
git add .
git commit -m "Final Railway deployment prep"
git push origin main
```

## 3. Create the Railway Project

1. Open Railway.
2. Click `New Project`.
3. Choose `Deploy from GitHub repo`.
4. Select this repository.
5. Railway will create a web service for the Django app.

## 4. Provision PostgreSQL

1. In the same Railway project, create a PostgreSQL service.
2. Wait until Railway provisions the database.
3. Open the PostgreSQL service and confirm that `DATABASE_URL` is available.

## 5. Attach a Persistent Volume for Media

The production settings expect uploaded media to be stored at `/app/media`.

1. Open the Railway Django web service.
2. Open `Settings`.
3. Open `Volumes`.
4. Add a volume mounted exactly at:

```text
/app/media
```

- Save the volume configuration.
- Redeploy after attaching the volume.

## 6. Configure Railway Environment Variables

Open the Django web service and add these variables:

```env
DJANGO_ENV=production
DJANGO_SECRET_KEY=<paste-a-new-random-secret>
DJANGO_ALLOWED_HOSTS=<your-service>.up.railway.app,.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://<your-service>.up.railway.app
DATABASE_URL=${{Postgres.DATABASE_URL}}
DB_CONN_MAX_AGE=600
DB_SSL_REQUIRE=True
DJANGO_MEDIA_URL=/media/
DJANGO_MEDIA_ROOT=/app/media
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=True
DJANGO_SECURE_HSTS_PRELOAD=True
```

Optional but useful:

```env
RAILWAY_PUBLIC_DOMAIN=<your-service>.up.railway.app
```

Important notes:

- `DJANGO_ENV=production` is required because `settings.py` switches on this value.
- `DATABASE_URL` is required because `production.py` reads it with `env_required('DATABASE_URL')`.
- `DJANGO_SECRET_KEY` is required because `production.py` reads it with `env_required('DJANGO_SECRET_KEY')`.
- `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` should match the final Railway public domain you actually use.

## 7. Generate the Production Secret Key

Generate the key locally:

```bash
source myenv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output into Railway as `DJANGO_SECRET_KEY`.

Security reminders:

- do not commit the real secret key
- do not reuse your local development key in production
- keep `.env.example` as a template only

## 8. What Railway Will Run Automatically

Railway uses these root files during deployment.

### requirements.txt

```txt
Django==5.2.11
Pillow==12.1.0
dj-database-url==2.3.0
gunicorn==23.0.0
psycopg2-binary==2.9.10
python-dotenv==1.0.1
whitenoise==6.9.0
```

### Procfile

```procfile
web: python manage.py collectstatic --noinput && gunicorn canteen_management.wsgi:application --bind 0.0.0.0:$PORT --log-file -
```

### runtime.txt

```txt
python-3.12.3
```

## 9. First Deployment Log Check

After the first deploy, inspect the deployment logs and confirm:

- dependencies installed successfully
- `collectstatic` completed successfully
- Gunicorn started without import errors
- there is no `ImproperlyConfigured` error for `DATABASE_URL` or `DJANGO_SECRET_KEY`
- there is no static manifest error from WhiteNoise startup

## 10. Run Migrations and Seed Production Data

After the application deploys successfully, run the production database setup inside the Railway web service environment.

### Option A: Railway Dashboard Shell

1. Open the web service.
2. Open the latest deployment.
3. Open the service shell.
4. Run:

```bash
python manage.py migrate
python manage.py loaddata data-migration.json
python manage.py check --deploy
```

### Option B: Railway CLI

Install Railway CLI, log in, then run:

```bash
railway login
railway link
railway shell
python manage.py migrate
python manage.py loaddata data-migration.json
python manage.py check --deploy
exit
```

## 11. Manual Media Re-Upload Warning

This is required for production correctness.

- `data-migration.json` contains database rows, not the binary image files from your local machine
- uploaded media is not pushed to GitHub
- Railway starts with a fresh empty volume until you upload files into it

That means your existing item images will not appear automatically on Railway even if the database fixture loads correctly.

After deployment, use the live admin inventory edit form to re-upload the existing menu item images so they are stored inside the mounted Railway volume at `/app/media`.

If you skip this step:

- image paths may exist in the database
- but the actual files will not exist on the production filesystem
- item images may return missing-file responses

## 12. Post-Deploy Verification Checklist

Verify all of the following in production:

1. The home page loads on the Railway public domain.
2. Login works for admin and normal users.
3. Menu items load from PostgreSQL data.
4. Checkout completes and reduces stock correctly.
5. Admin inventory, analytics, and orders pages load without route errors.
6. AJAX refreshes continue working silently.
7. You can upload a new item image.
8. Uploaded images still exist after a redeploy.
9. Static assets load correctly.
10. Receipt pages open for paid orders.

## 13. Common Problems and Fixes

### App crashes on boot

Check:

- `DJANGO_ENV=production`
- `DJANGO_SECRET_KEY` is set
- `DATABASE_URL` is mapped from the PostgreSQL service
- `DJANGO_ALLOWED_HOSTS` matches the Railway hostname you are using

### CSRF failure on forms

Check:

- `DJANGO_CSRF_TRUSTED_ORIGINS` contains the full `https://...` origin
- you are using the final Railway public URL, not an old preview URL

### Uploaded images disappear after redeploy

Check:

- the volume is mounted at `/app/media`
- `DJANGO_MEDIA_ROOT=/app/media`
- the images were uploaded after the volume was attached

### Static files return 404

Check:

- `whitenoise` is installed
- `collectstatic` succeeded in the logs
- there is no manifest generation error during startup

### `python manage.py loaddata data-migration.json` fails

Check:

- migrations were run first
- the fixture file exists at the repository root
- the database schema matches the current models and migrations
