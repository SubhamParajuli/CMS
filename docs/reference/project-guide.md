# Project guide

The Canteen Management System lets students and teachers order from a menu while staff manage inventory and review sales. It uses Django 5.2.11, Python 3.12, Django templates, Bootstrap, and vanilla JavaScript. Local settings default to SQLite; production settings support PostgreSQL.

## Application structure

| App | Responsibility |
| --- | --- |
| `accounts/` | Custom user model, roles, and unique five-digit user codes |
| `home/` | Login, registration, staff inventory forms, order dashboard, and sales analytics |
| `inventory/` | Menu items, stock, images, availability, and customer menu responses |
| `orders/` | Order headers, line items, checkout validation, and stock updates |
| `payments/` | Cash payment records, receipts, and payment consistency checks |
| `canteen_management/` | Settings, URLs, WSGI/ASGI entry points, and production media serving |

Templates live with their apps. Shared static files are under `public/static/`. Uploaded images default to `public/media/` locally; new uploads are ignored by Git, while some older sample images remain tracked. The [directory layout](directory-layout.txt) shows the main paths.

## Accounts and access

Users have an `admin`, `student`, or `teacher` role. Registration creates student or teacher accounts. Staff views require a canteen admin, and `createsuperuser` creates an admin account. Each user needs a unique five-digit `user_code`.

The user model validates the role and code when saving. The database also has a valid-role check and unique constraints on the username and code. The five-digit format check is model validation rather than a database check.

## Checkout

The menu builds a cart in the browser and sends item IDs and quantities to `POST /checkout/`. The server reads prices from inventory rather than accepting a client-supplied total.

Checkout validates stock inside `transaction.atomic()`, creates an order and its line items, reduces stock, records a cash payment, creates a receipt, and marks the order paid. Each line stores `price_at_purchase` so later menu price changes do not change the recorded price.

The inventory query uses `select_for_update()`. PostgreSQL locks those rows until the transaction completes; SQLite does not provide the same row-locking behavior. Local SQLite tests do not establish production concurrency behavior.

Payment records represent cash transactions. There is no online payment gateway or external payment confirmation.

## Main routes

| Route | Purpose |
| --- | --- |
| `/` | Landing page |
| `/login/`, `/register/`, `/logout/` | Account access |
| `/menu/` | Customer menu and cart |
| `/api/inventory/` | Customer inventory snapshot |
| `/checkout/` | Checkout, authenticated POST requests |
| `/receipt/<order_id>/` | Receipt for an authorized user |
| `/admin_page/` | Staff inventory dashboard |
| `/admin_page/update_item/<item_id>/` | Edit a menu item |
| `/admin_page/delete_item/<item_id>/` | Delete a menu item through POST |
| `/admin_page/analytics/` | Staff sales analytics |
| `/admin_page/orders/` | Staff order history |
| `/admin/` | Django administration |

The staff pages also expose JSON snapshots under `/admin_page/api/inventory/`, `/admin_page/analytics/api/`, and `/admin_page/orders/api/`. The menu, analytics, and orders pages refresh data periodically.

## Configuration and maintenance

`canteen_management/settings.py` selects `local.py` or `production.py` from the process environment variable `DJANGO_ENV`. Both import shared settings from `base.py`, which loads a local `.env` when present. Set `DJANGO_ENV=production` in the hosting service environment before starting Django.

Local setup is in the [README](../../README.md); hosted configuration is in the [deployment guide](../deployment.md). The optional `sample_menu` fixture contains menu items only and is intended for a fresh local demo. Create accounts through registration or `createsuperuser`.

Run checks from the repository root:

```sh
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

To inspect payment and receipt consistency without changing records:

```sh
python manage.py payment_consistency --fail-on-issues
```

The command also has a `--repair` option that creates missing records for paid orders and synchronizes mismatched amounts. Review its output and back up the database before using that option.

Model and migration files are the source for schema changes. See the [database reference](../database/README.md) for relationships and the limits of the accompanying SQL examples.
