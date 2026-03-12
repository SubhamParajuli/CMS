# Canteen Management System

Updated: 2026-03-12

This repository contains a Django-based Canteen Management System built for role-based campus food ordering and canteen administration. The project supports local development with SQLite or PostgreSQL and production deployment to Railway with PostgreSQL, WhiteNoise, Gunicorn, and persistent media storage.

Use this README as the primary setup, validation, and deployment reference for the project.

## Overview

The system is organized around four main Django apps:

- `accounts`: custom users, 5-digit user codes, and role management for `admin`, `student`, and `teacher`
- `inventory`: menu item storage, categories, pricing, stock, and item image handling
- `orders`: cart checkout, order creation, and order-item line records
- `payments`: payment records, receipts, and payment consistency checks

Key interface behaviors:

- an authenticated customer menu page
- silent AJAX polling for live inventory refresh
- a custom admin dashboard for inventory management
- live admin analytics and order monitoring
- image upload controls with clear/remove behavior for menu item forms

## Technology Stack

- Python 3.12.3
- Django 5.2.11
- SQLite for default local development
- PostgreSQL for Railway production
- WhiteNoise for static file delivery
- Gunicorn for production serving
- Pillow for uploaded image support
- Vanilla JavaScript for cart behavior and AJAX polling

## Project Structure

```text
/home/suhan/CMS/
├── accounts/
├── canteen_management/
│   ├── base.py
│   ├── local.py
│   ├── media_views.py
│   ├── production.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── home/
├── inventory/
├── orders/
├── payments/
├── public/
│   ├── media/
│   └── static/
├── data-migration.json
├── DEPLOYMENT_GUIDE.md
├── DBMS_VIVA_GUIDE.md
├── Procfile
├── README.md
├── PROJECT_DETAILED_DOCUMENTATION.md
├── PROJECT_DIRECTORY_DOCUMENTATION.txt
├── manage.py
├── requirements.txt
└── runtime.txt
```

## Core Features

- Role-based authentication with custom user roles
- Admin-only inventory management and item editing
- Menu item image upload with preview and clear/remove controls
- Checkout flow with transactional stock updates
- Automatic payment and receipt record creation during checkout
- Sales analytics and order dashboards with silent background refresh
- Railway-ready production configuration using PostgreSQL and persistent media storage

## Data Model Summary

The implemented relational design in this project is:

- `CustomUser` 1-to-many `Order`
- `Order` 1-to-many `OrderItem`
- `Inventory` 1-to-many `OrderItem`
- `Order` 1-to-1 `Payment`
- `Order` 1-to-1 `Receipt`

This structure keeps user data, menu items, orders, payments, and receipts separated while preserving referential integrity.

## Settings Architecture

This project now uses a split settings layout:

- `canteen_management/settings.py`: environment switcher
- `canteen_management/base.py`: shared Django settings
- `canteen_management/local.py`: local development configuration
- `canteen_management/production.py`: Railway-safe production configuration

Environment selection is controlled through `DJANGO_ENV`.

- `DJANGO_ENV=local` loads local development settings
- `DJANGO_ENV=production` loads production settings

## Local Installation

### 1. Create and activate a virtual environment

```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a local environment file

```bash
cp .env.example .env
```

### 4. Configure local settings

Use `DJANGO_ENV=local` and provide a secret key in `.env`.

```env
DJANGO_ENV=local
DJANGO_SECRET_KEY=replace-with-a-real-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DB_CONN_MAX_AGE=600
DB_SSL_REQUIRE=False
DJANGO_MEDIA_URL=/media/
DJANGO_MEDIA_ROOT=/home/your-user/CMS/public/media
```

### 5. Choose your local database

Default local mode uses SQLite automatically if `DATABASE_URL` is not set.

Optional local PostgreSQL example:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/canteen_management
```

Tests default to SQLite unless you explicitly set `TEST_DATABASE_URL`.

```env
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/canteen_management_test
```

### 6. Apply migrations and start the app

```bash
python manage.py migrate
python manage.py runserver
```

## AJAX and Silent Live Refresh

The project does not use WebSockets. It uses silent AJAX polling every 10 seconds in the browser while keeping the UI clean.

Live-refresh endpoints:

- `/api/inventory/` for customer menu stock refresh
- `/admin_page/api/inventory/` for admin inventory dashboard refresh
- `/admin_page/analytics/api/` for admin analytics refresh
- `/admin_page/orders/api/` for admin orders refresh

The polling remains active without visible status text in the templates.

## Image Upload Behavior

Admin item forms use a custom file input widget:

- add-item form supports clearing a newly selected file before submit
- update-item form supports clearing a new selection
- update-item form also supports removing the currently stored image

Uploaded files are validated for extension and size, and the UI shows preview cards where appropriate.

## Railway Deployment Files

The root deployment files used by Railway are:

- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `data-migration.json`

Current production dependencies include:

- `dj-database-url`
- `gunicorn`
- `psycopg2-binary`
- `python-dotenv`
- `whitenoise`

## Step-by-Step Railway Deployment

### 1. Push the project to GitHub

Make sure the repository includes:

- source code
- `Procfile`
- `runtime.txt`
- `requirements.txt`
- `data-migration.json`

Make sure the repository does not include:

- `.env`
- local `media/` files
- local SQLite database files intended only for development

### 2. Create the Railway project

1. Open Railway.
2. Click `New Project`.
3. Choose `Deploy from GitHub repo`.
4. Select this repository.
5. Railway will create a web service for the Django app.

### 3. Provision PostgreSQL

1. In the same Railway project, create a new PostgreSQL service.
2. Wait for Railway to generate the PostgreSQL connection variables.
3. Confirm that the database service exposes `DATABASE_URL`.

### 4. Add a persistent volume for media

1. Open the Railway Django web service.
2. Go to `Settings`.
3. Open `Volumes`.
4. Add a volume mounted exactly at:

```text
/app/media
```

This matches the production setting `DJANGO_MEDIA_ROOT=/app/media`.

### 5. Configure Railway environment variables

Add these variables to the Django web service:

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

Optional:

```env
RAILWAY_PUBLIC_DOMAIN=<your-service>.up.railway.app
```

### 6. Generate a production secret key

Run locally:

```bash
source myenv/bin/activate
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key into Railway as `DJANGO_SECRET_KEY`.

### 7. Run the first production database setup

Using the Railway service shell or Railway CLI, run:

```bash
python manage.py migrate
python manage.py loaddata data-migration.json
python manage.py check --deploy
```

CLI sequence:

```bash
railway login
railway link
railway shell
python manage.py migrate
python manage.py loaddata data-migration.json
python manage.py check --deploy
exit
```

### 8. Re-upload existing item images manually

Operational note:

`data-migration.json` stores database records, not the binary image files from your local machine. Because uploaded media is not pushed to GitHub, your existing item images must be uploaded again from the live admin UI after the Railway volume is attached.

If you skip this step:

- the inventory rows may still reference image paths
- but the physical image files will be missing in production

## Production Verification Checklist

Before final submission or viva, verify these items on Railway:

1. Home page loads correctly.
2. Login works for both admin and normal users.
3. Menu items load from PostgreSQL.
4. Checkout completes and reduces stock correctly.
5. Inventory, analytics, and orders admin pages load without route errors.
6. Static files are served correctly.
7. Uploaded images survive redeploys because the volume is mounted.
8. Receipt pages open for paid orders.

## Local Verification Commands

Run these before pushing:

```bash
source myenv/bin/activate
python manage.py check
python manage.py makemigrations --check
python manage.py test
python manage.py collectstatic --noinput
```

## Documentation

- `PROJECT_DETAILED_DOCUMENTATION.md` contains the full project explanation
- `PROJECT_DIRECTORY_DOCUMENTATION.txt` explains the current repository layout
- `DBMS_VIVA_GUIDE.md` maps this project directly to DBMS syllabus topics
- `DEPLOYMENT_GUIDE.md` contains a Railway-focused deployment guide
