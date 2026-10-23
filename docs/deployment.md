# Deployment

The app has production settings for PostgreSQL, Gunicorn, and WhiteNoise. The root `Procfile` collects static files and starts Gunicorn on the hosting service's `PORT`. `runtime.txt` specifies Python 3.12.3; dependencies are in `requirements.txt`.

## Configure the service

On Railway, connect the GitHub repository to a web service, add PostgreSQL, and attach a persistent volume at `/app/media` for uploaded images. See Railway's [Django guide](https://docs.railway.com/guides/django) and [volume documentation](https://docs.railway.com/volumes) for the service setup.

Set these variables on the web service, replacing the example domain and secret:

```env
DJANGO_ENV=production
DJANGO_SECRET_KEY=<a-new-random-secret>
DJANGO_ALLOWED_HOSTS=your-service.up.railway.app
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-service.up.railway.app
DATABASE_URL=<your-PostgreSQL-connection-URL>
DJANGO_MEDIA_ROOT=/app/media
DJANGO_MEDIA_URL=/media/
```

Use the database service's `DATABASE_URL` reference rather than copying credentials into the repository. The settings default `DB_SSL_REQUIRE` to `True`; set it to match the connection requirements of your database service. `DB_CONN_MAX_AGE` defaults to 600 seconds.

`DJANGO_ENV` must be set in the process environment. The settings selector reads it before the shared settings load `.env`, so putting `DJANGO_ENV=production` only in a file does not select production settings.

Generate a secret locally with:

```sh
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Production settings disable debug mode and enable secure cookies, HTTPS redirects, and HSTS. `RAILWAY_PUBLIC_DOMAIN`, when present, supplies the default allowed host and CSRF origin. Explicit host and origin variables override those defaults.

## Initialize the database

Open a shell in the running web container using your hosting provider's remote access tools. On Railway, [SSH](https://docs.railway.com/cli/ssh) connects to the deployed service. Run these commands with the service's production variables available:

```sh
python manage.py migrate
python manage.py createsuperuser
python manage.py check --deploy
```

Enter a unique five-digit `user_code` when creating the admin account. Add the real menu through `/admin_page/`; a fresh installation does not need an exported database dump.

For a fresh local demonstration database only, `python manage.py loaddata sample_menu` adds four synthetic menu items. It uses fixed primary keys and can replace matching items, so do not load it into a populated production database.

## Static files and images

The start command runs `collectstatic`; WhiteNoise serves the resulting `staticfiles/` directory. Uploaded images use a separate media directory and are served by `canteen_management/media_views.py` in production.

Upload menu images through the staff dashboard after the volume is attached. Database backups contain image paths, so keep a separate backup of the files in `/app/media`. The menu fixture does not include image files. The repository retains some older sample images, but it is not a backup of deployed uploads.

## Verify the deployment

Check login and registration, create a menu item, place a test order, open its receipt, and review staff order history and sales analytics. Confirm that static assets load and that a new image remains available after a redeploy.

If startup fails, check the deployment log for missing `DJANGO_SECRET_KEY` or `DATABASE_URL`, dependency errors, and `collectstatic` failures. For rejected forms, check the exact HTTPS origin in `DJANGO_CSRF_TRUSTED_ORIGINS`. For missing images, check that the volume mount matches `DJANGO_MEDIA_ROOT` and the image file exists there.
