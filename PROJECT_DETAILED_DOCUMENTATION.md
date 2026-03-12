# Canteen Management System - Detailed Project Documentation

Updated: 2026-03-12
Workspace: `/home/suhan/CMS`

## 1. Project Summary

This document presents the technical structure and operational design of a Django-based Canteen Management System intended for campus canteen or POS-style ordering. The system supports role-based access, inventory administration, checkout processing, payment tracking, receipt generation, and Railway deployment with PostgreSQL.

Supported roles:

- `student`
- `teacher`
- `admin`

Students and teachers use the ordering flow. Admins manage inventory and access analytics and order-monitoring features.

## 2. Current Repository Layout

The project uses a root-level Django layout.

```text
/home/suhan/CMS/
├── accounts/
├── canteen_management/
├── home/
├── inventory/
├── orders/
├── payments/
├── public/
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

Key repository facts:

- `manage.py` is at the repository root.
- app folders are also at the repository root.
- the Django configuration package is `canteen_management`.
- old nested references like `canteen_management/home/...` are outdated.

## 3. Technology Stack

- Python 3.12.3
- Django 5.2.11
- SQLite for default local development and tests
- PostgreSQL for Railway production
- WhiteNoise for static file serving in production
- Gunicorn for Railway runtime
- Pillow for image uploads
- Bootstrap and Font Awesome in the templates
- Vanilla JavaScript for cart interactions and AJAX polling

## 4. Configuration Package

Path:

- `canteen_management/`

Key configuration files:

- `canteen_management/settings.py`
- `canteen_management/base.py`
- `canteen_management/local.py`
- `canteen_management/production.py`
- `canteen_management/urls.py`
- `canteen_management/media_views.py`
- `canteen_management/asgi.py`
- `canteen_management/wsgi.py`

### 4.1 Settings Split

The project now uses a split settings architecture.

- `settings.py`: selects local or production settings using `DJANGO_ENV`
- `base.py`: shared apps, middleware, templates, auth model, static, and common utilities
- `local.py`: local development database, hosts, CSRF origins, and local media path
- `production.py`: PostgreSQL parsing via `dj-database-url`, WhiteNoise manifest storage, secure cookies, HSTS, SSL redirect, and Railway media path

### 4.2 Important Runtime Facts

- `BASE_DIR` resolves to `/home/suhan/CMS`
- `AUTH_USER_MODEL = 'accounts.CustomUser'`
- local static source is `/home/suhan/CMS/public/static`
- local media path defaults to `/home/suhan/CMS/public/media`
- production media path is `/app/media`
- production static files are served through WhiteNoise

## 5. Deployment Files

The project includes the production files Railway expects at the root:

- `requirements.txt`
- `Procfile`
- `runtime.txt`
- `data-migration.json`

### 5.1 requirements.txt

Production dependency set:

- `Django==5.2.11`
- `dj-database-url==2.3.0`
- `gunicorn==23.0.0`
- `psycopg2-binary==2.9.10`
- `python-dotenv==1.0.1`
- `whitenoise==6.9.0`
- `Pillow==12.1.0`

### 5.2 Procfile

The Railway web process runs:

```procfile
web: python manage.py collectstatic --noinput && gunicorn canteen_management.wsgi:application --bind 0.0.0.0:$PORT --log-file -
```

### 5.3 runtime.txt

The Python runtime is pinned to:

```text
python-3.12.3
```

### 5.4 data-migration.json

This fixture is intended for seeding Railway PostgreSQL after running migrations in production.

## 6. App Responsibilities

### 6.1 accounts

Path:

- `accounts/`

Purpose:

- custom user model
- role validation
- 5-digit `user_code` validation
- admin/staff behavior management

Important file:

- `accounts/models.py`

Key rules implemented:

- valid roles are `admin`, `student`, and `teacher`
- superusers are forced to use the `admin` role
- `user_code` must be exactly 5 digits
- admin users are treated as staff users

### 6.2 inventory

Path:

- `inventory/`

Purpose:

- stores menu items
- stores categories, price, quantity, availability, and optional images
- powers the authenticated menu page

Important files:

- `inventory/models.py`
- `inventory/views.py`
- `inventory/templates/menu.html`

Current `Inventory` fields:

- `item_name`
- `category`
- `price`
- `quantity`
- `food_image`
- `is_available`

### 6.3 orders

Path:

- `orders/`

Purpose:

- stores master orders and line items
- performs transactional checkout
- updates stock after successful purchase

Important files:

- `orders/models.py`
- `orders/views.py`
- `orders/tests.py`

Implemented order model relationships:

- `Order.user` links each order to one user
- `OrderItem.order` links line items to one order
- `OrderItem.item` links line items to one inventory item
- checkout uses `transaction.atomic()` and `select_for_update()` to preserve consistency

### 6.4 payments

Path:

- `payments/`

Purpose:

- stores payment records
- stores receipts
- renders paid order receipts
- provides a management command to audit payment consistency

Important files:

- `payments/models.py`
- `payments/views.py`
- `payments/templates/receipt.html`
- `payments/management/commands/payment_consistency.py`

Current design:

- one `Payment` per `Order`
- one `Receipt` per `Order`

### 6.5 home

Path:

- `home/`

Purpose:

- landing page
- login and registration
- logout
- inventory admin dashboard
- update item form
- admin analytics dashboard
- admin orders dashboard
- form and widget definitions

Important files:

- `home/forms.py`
- `home/views.py`
- `home/templates/admin.html`
- `home/templates/update_admin.html`
- `home/templates/admin_analytics.html`
- `home/templates/admin_orders.html`
- `home/templates/widgets/admin_image_input.html`

## 7. Main Routes

Defined in `canteen_management/urls.py`.

Primary routes:

- `/` -> landing page
- `/login/` -> login page
- `/register/` -> registration page
- `/logout/` -> logout action
- `/menu/` -> authenticated customer menu
- `/api/inventory/` -> customer inventory JSON snapshot
- `/checkout/` -> checkout endpoint
- `/receipt/<order_id>/` -> receipt page
- `/admin_page/` -> custom inventory dashboard
- `/admin_page/api/inventory/` -> admin inventory JSON snapshot
- `/admin_page/analytics/` -> sales analytics page
- `/admin_page/analytics/api/` -> analytics JSON snapshot
- `/admin_page/orders/` -> admin orders page
- `/admin_page/orders/api/` -> admin orders JSON snapshot
- `/admin_page/update_item/<item_id>/` -> update item page
- `/admin_page/delete_item/<item_id>/` -> delete item action
- `/admin/` -> Django admin

## 8. Access Control

### Admin access

Admins are users with:

- `role='admin'`, or
- `is_superuser=True`

Admin-only views are protected through `admin_required`.

Admins can access:

- inventory dashboard
- analytics dashboard
- orders dashboard
- item update and delete actions
- Django admin

### Student and teacher access

Students and teachers can:

- register through `/register/`
- log in through `/login/`
- browse `/menu/`
- add items to cart
- check out
- open their own receipts

They cannot access the custom admin pages.

## 9. Forms and Validation

### 9.1 RegistrationForm

Location:

- `home/forms.py`

Validation rules:

- role must be `student` or `teacher`
- `user_code` must be unique and exactly 5 digits
- username must be unique
- password confirmation must match
- password uses Django password validators

### 9.2 InventoryItemForm

Location:

- `home/forms.py`

Validation rules implemented:

- item name is required
- item name must be at least 2 characters long
- item name must be unique case-insensitively
- price must be a positive whole rupee amount
- quantity cannot be negative
- uploaded image extension must be supported
- uploaded image size must be 5 MB or smaller
- if quantity is `0` or less, `is_available` is forced off during cleaning

## 10. Recent UI and Admin Improvements

The current UI behavior reflects recent admin improvements in the templates and forms.

### 10.1 Image input improvements

The custom `AdminImageInput` widget provides:

- `Clear Selection` for new file choices
- `Remove current image` for existing images
- file-name display for the selected replacement image
- dedicated preview behavior on the update page

### 10.2 Silent AJAX refresh

The menu page, analytics page, and orders page use AJAX polling every 10 seconds without displaying visible polling text.

### 10.3 Admin quick edit workflow

The admin inventory dashboard contains:

- inventory table
- quick edit panel
- dedicated full update page
- live dashboard stats

## 11. Core Business Flows

### 11.1 Login flow

View:

- `home.views.login_page`

Behavior:

1. authenticates username and password
2. redirects admins to `/admin_page/`
3. redirects normal users to `/menu/`
4. preserves safe `next` redirects when applicable

### 11.2 Registration flow

View:

- `home.views.register_page`

Behavior:

- creates student or teacher accounts only
- redirects successful registrations to the login page

### 11.3 Inventory admin flow

Views:

- `home.views.admin_page`
- `home.views.admin_update_item`
- `home.views.admin_delete_item`

Behavior:

- add new items
- update existing items
- delete items through POST-only action
- filter and sort inventory
- expose JSON snapshot data for silent refresh

### 11.4 Checkout flow

View:

- `orders.views.checkout`

Behavior:

1. receives cart JSON
2. normalizes and validates quantities
3. locks inventory rows with `select_for_update()`
4. creates the `Order`
5. creates each `OrderItem`
6. decreases item stock
7. creates `Payment`
8. creates `Receipt`
9. marks the order as paid

This flow is wrapped inside `transaction.atomic()` so partial order states are avoided.

### 11.5 Analytics flow

Views:

- `home.views.admin_sales_analytics`
- `home.views.admin_sales_analytics_snapshot`

Behavior:

- aggregates daily, weekly, and monthly sales
- calculates best-selling items
- calculates top customers
- exposes JSON snapshot responses for live UI refresh

## 12. Static and Media Handling

### Local development

- static source directory: `/home/suhan/CMS/public/static`
- media upload directory: `/home/suhan/CMS/public/media`

### Production on Railway

- static files are collected to `STATIC_ROOT`
- WhiteNoise serves static files
- media files are stored under `/app/media`
- missing media in production is served via `canteen_management.media_views.serve_production_media`

## 13. Railway Deployment Notes

This codebase is configured for Railway without Docker.

Production requirements use the same Railway variable names documented in `README.md` and `DEPLOYMENT_GUIDE.md`.

Required production environment variables:

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

Deployment sequence:

1. Provision Railway PostgreSQL.
2. Attach a Railway volume mounted at `/app/media`.
3. Add the production environment variables shown above.
4. Let Railway deploy using `Procfile`, `runtime.txt`, and `requirements.txt`.
5. Run the production database setup commands.

Required production commands:

```bash
python manage.py migrate
python manage.py loaddata data-migration.json
python manage.py check --deploy
```

Production media note:

- database fixture data can be loaded from `data-migration.json`
- binary image files are not stored inside the fixture
- existing menu item images must be re-uploaded from the live admin UI after deployment so they are stored in the mounted Railway volume at `/app/media`

## 14. Verified State

Validated on 2026-03-12:

- `python manage.py check` passes
- `python manage.py makemigrations --check` reports no changes
- `python manage.py test` passes with 51 tests
- main admin, menu, orders, analytics, and receipt flows are covered by tests

## 15. Important Files For Ongoing Maintenance

- `manage.py`
- `canteen_management/settings.py`
- `canteen_management/base.py`
- `canteen_management/local.py`
- `canteen_management/production.py`
- `canteen_management/urls.py`
- `canteen_management/media_views.py`
- `accounts/models.py`
- `home/forms.py`
- `home/views.py`
- `home/templates/admin.html`
- `home/templates/update_admin.html`
- `home/templates/admin_analytics.html`
- `home/templates/admin_orders.html`
- `home/templates/widgets/admin_image_input.html`
- `inventory/models.py`
- `inventory/views.py`
- `inventory/templates/menu.html`
- `orders/models.py`
- `orders/views.py`
- `payments/models.py`
- `payments/views.py`
- `payments/templates/receipt.html`
- `payments/management/commands/payment_consistency.py`
