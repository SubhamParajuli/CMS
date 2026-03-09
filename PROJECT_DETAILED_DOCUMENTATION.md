# Canteen Management System - Detailed Project Documentation

Updated: 2026-03-10
Workspace: `/home/suhan/CMS`

## 1. Project Purpose

This is a Django-based canteen management system built for three main user groups:

- `students` who browse the menu, add items to cart, check out, and view receipts
- `teachers` who use the same customer ordering flow as normal users
- `admins` who manage inventory from a custom dashboard and can also access Django admin

The project combines:

- custom authentication with role-based access
- inventory and menu management
- cart and checkout logic
- payment and receipt persistence
- static/media image handling
- automated test coverage for major business rules

## 2. Technology Stack

- Backend framework: Django 5.2.11
- Language: Python
- Database: SQLite
- Image support: Pillow
- Frontend: Django templates, Bootstrap classes, Font Awesome icons, vanilla JavaScript
- Local persistence on menu page: `localStorage`

## 3. High-Level Architecture

The project is split into five Django apps:

- `accounts`
  Handles the custom user model and role logic.
- `home`
  Handles authentication pages and the custom admin dashboard.
- `inventory`
  Handles menu item records and the customer menu page.
- `orders`
  Handles order creation and checkout.
- `payments`
  Handles payment rows, receipts, receipt rendering, and payment auditing.

The project-level `canteen_management` package holds global settings, URL routing, and the WSGI/ASGI entry points.

## 4. User Roles and Access Rules

### Admin

Admin users are defined through the custom user model with:

- `role='admin'`, or
- `is_superuser=True`

The project exposes two admin surfaces:

- `/admin_page/`
  This is the custom canteen dashboard for inventory management.
- `/admin/`
  This is the default Django admin site.

Custom admin routes are protected by the `admin_required` decorator in `home/views.py`.

### Student and Teacher

Students and teachers:

- can register through the public registration page
- can log in through `/login/`
- can browse `/menu/`
- can check out and view their own receipts
- cannot access the custom admin dashboard

### Registration Policy

Public registration only allows:

- `student`
- `teacher`

The `admin` role cannot be created from the public registration form.

## 5. Data Model

### 5.1 CustomUser

Defined in `accounts/models.py`.

Important fields:

- `username`
- `password`
- `user_code`
- `role`
- `is_staff`
- `is_superuser`

Business rules:

- `user_code` must be exactly 5 digits
- `role` must be one of:
  - `admin`
  - `student`
  - `teacher`
- admin users are treated as staff
- superusers are forced to use the admin role

Why this matters:

- the project uses `role` as the main canteen authorization signal
- Django admin compatibility still depends on `is_staff` and `is_superuser`

### 5.2 Inventory

Defined in `inventory/models.py`.

Fields:

- `item_name`
- `category`
- `price`
- `quantity`
- `food_image`
- `is_available`

Meaning:

- `quantity` is current stock
- `is_available` controls whether the item appears in the customer menu

### 5.3 Order

Defined in `orders/models.py`.

Fields:

- `user`
- `order_date`
- `total_amount`
- `is_paid`

Meaning:

- one order belongs to one user
- an order is marked paid only after successful payment/receipt creation in checkout

### 5.4 OrderItem

Defined in `orders/models.py`.

Fields:

- `order`
- `item`
- `quantity`
- `price_at_purchase`

Meaning:

- stores a snapshot of what was bought and at what price

### 5.5 Payment

Defined in `payments/models.py`.

Fields:

- `order`
- `payment_method`
- `amount_paid`
- `payment_time`

Current payment method default:

- `CASH`

### 5.6 Receipt

Defined in `payments/models.py`.

Fields:

- `order`
- `generated_at`

Meaning:

- each paid order should have exactly one payment and one receipt

## 6. Core Request Flows

### 6.1 Landing Page

Route:

- `/`

Behavior:

- renders the entry page for the system
- links users toward login

### 6.2 Login Flow

Route:

- `/login/`

View:

- `home.views.login_page`

Behavior:

1. User submits `username` and `password`.
2. Django authenticates credentials.
3. If valid:
   - canteen admin -> redirect to `/admin_page/`
   - normal user -> redirect to `/menu/`
4. If invalid:
   - error message is shown on the login page

Special note:

- a legacy-login fix was added so a bad old user record does not crash when Django updates `last_login`

### 6.3 Registration Flow

Route:

- `/register/`

View:

- `home.views.register_page`

Form:

- `home.forms.RegistrationForm`

Validation rules:

- role must be `student` or `teacher`
- `user_code` must be exactly 5 digits
- `user_code` must be unique
- username must be unique
- password is checked with Django password validators

Result:

- valid form creates the user and redirects to `/login/`

### 6.4 Customer Menu Flow

Route:

- `/menu/`

View:

- `inventory.views.inventory_list`

Behavior:

- login required
- only available items are shown
- menu page uses JavaScript cart logic stored in `localStorage`

UI features:

- quantity increment/decrement controls
- add-to-cart buttons
- cart count and total
- mobile-friendly stacked layout
- fallback images for missing uploads
- safer cart rendering with DOM APIs instead of HTML string templates

### 6.5 Checkout Flow

Route:

- `/checkout/`

View:

- `orders.views.checkout`

Method:

- POST only

Payload:

- JSON body containing a `cart` object

Important checkout rules:

- cart must not be empty
- quantities must be integers
- quantity must be at least `1`
- each item must still exist
- each item must still be available
- stock must be sufficient

Database behavior:

- inventory rows are locked during validation
- the full operation runs inside a transaction
- the system creates:
  - `Order`
  - `OrderItem` rows
  - `Payment`
  - `Receipt`
- stock is decremented only within the same atomic flow
- if any step fails, the entire transaction rolls back

Successful response:

- JSON response containing `success: true` and `order_id`

### 6.6 Receipt Flow

Route:

- `/receipt/<order_id>/`

View:

- `payments.views.receipt_view`

Rules:

- login required
- order must belong to the current user
- order must already be paid
- payment row must exist
- receipt row must exist

This view no longer auto-creates missing receipts. Missing payment or receipt data is treated as an integrity problem.

### 6.7 Admin Inventory Flow

Routes:

- `/admin_page/`
- `/admin_page/update_item/<item_id>/`
- `/admin_page/delete_item/<item_id>/`

Views:

- `home.views.admin_page`
- `home.views.admin_update_item`
- `home.views.admin_delete_item`

Rules:

- admin-only access
- anonymous users are redirected to `/login/`
- non-admin logged-in users are redirected to `/menu/`
- delete is POST-only
- CSRF token is required for delete and form submissions

Dashboard features:

- inventory table
- add item form
- edit item page
- delete action with confirmation
- quick stats card showing:
  - total items
  - available items
  - low stock items

## 7. Forms and Validation

### 7.1 RegistrationForm

Located in `home/forms.py`.

Purpose:

- protects registration from invalid roles, duplicate usernames, duplicate user codes, and weak password input

### 7.2 InventoryItemForm

Located in `home/forms.py`.

Purpose:

- validates admin inventory create/update operations

Validation includes:

- non-empty item name
- non-negative price
- non-negative quantity
- image extension checks
- image content type checks
- image size limit of 5 MB

## 8. Static and Media Handling

Current file strategy:

- static assets live under `canteen_management/public/static/`
- uploaded files live under `canteen_management/public/media/`

Why this matters:

- uploaded user/admin images are no longer mixed with static files
- templates use `item.food_image.url` when an image exists
- templates fall back to a static placeholder when no image exists or when an image fails to load

Current URLs:

- static files -> `/static/`
- media files -> `/media/`

## 9. Frontend and UI Behavior

### Landing and Auth Pages

Templates:

- `home/templates/index.html`
- `home/templates/login.html`
- `home/templates/register.html`

Purpose:

- entry experience, login, and registration

### Admin Dashboard UI

Template:

- `home/templates/admin.html`

Features:

- inventory table
- inline action buttons
- add-item form
- server-side validation error display
- quick stats card
- flash messages

### Admin Update UI

Template:

- `home/templates/update_admin.html`

Features:

- edit existing inventory data
- preview current image
- edit availability status

### Menu UI

Template:

- `inventory/templates/menu.html`

Features:

- responsive product grid
- cart sidebar
- stacked mobile behavior on smaller screens
- JS cart rendering
- fallback image support

## 10. Security and Integrity Improvements Already Applied

These are important because they shape how the system now behaves.

### Access Control

- admin dashboard access is restricted
- delete action is not exposed through GET anymore

### Checkout Integrity

- invalid quantities are blocked
- stock is validated before final commit
- partial order writes are prevented through transactions

### Payment Integrity

- payment and receipt creation happen in the checkout transaction
- receipt view requires real existing payment and receipt records

### Legacy Data Protection

- old blank admin roles were backfilled
- old invalid or blank user codes were backfilled
- login no longer crashes on legacy `last_login` updates

### Frontend Safety

- cart rows are created with DOM nodes, reducing XSS risk from client-side cart data
- menu image rendering has fallback behavior

## 11. Management Command

Command:

```bash
python manage.py payment_consistency
```

Purpose:

- audit the consistency between paid orders, payments, and receipts

Useful options:

```bash
python manage.py payment_consistency --repair
python manage.py payment_consistency --fail-on-issues
```

What it checks:

- paid orders missing payments
- paid orders missing receipts
- payment amount mismatches
- unpaid orders that still have payment rows
- unpaid orders that still have receipt rows

## 12. Tests

Current test modules:

- `accounts/tests.py`
- `home/tests.py`
- `inventory/tests.py`
- `orders/tests.py`
- `payments/tests.py`

Coverage includes:

- custom user role behavior
- admin-only route protection
- login redirect behavior
- legacy admin login safety
- registration validation
- inventory form validation
- image and media rendering
- safer menu rendering
- mobile layout markers
- checkout rollback behavior
- payment/receipt integrity
- management command behavior

At the time of the latest verified run, the suite passed with 36 tests.

## 13. Database and Migration Notes

The project currently uses SQLite:

- `canteen_management/db.sqlite3`

Important migrations in `accounts`:

- `0002_backfill_roles_and_add_role_constraint`
- `0003_backfill_invalid_user_codes`

Why they matter:

- they clean old bad user data so the current validation rules and login flow work reliably

If teammates pull fresh changes that include migrations, they should run:

```bash
python manage.py migrate
```

## 14. Current Development Characteristics

This project is currently configured as a development-focused Django project:

- `DEBUG=True`
- SQLite database
- committed local secret key in settings
- empty `ALLOWED_HOSTS`

That is acceptable for local academic/team development, but it is not a production-ready deployment setup.

## 15. Main Files to Study First

For someone trying to understand the project quickly, read these in order:

1. `canteen_management/canteen_management/settings.py`
2. `canteen_management/canteen_management/urls.py`
3. `canteen_management/accounts/models.py`
4. `canteen_management/home/forms.py`
5. `canteen_management/home/views.py`
6. `canteen_management/inventory/models.py`
7. `canteen_management/inventory/templates/menu.html`
8. `canteen_management/orders/models.py`
9. `canteen_management/orders/views.py`
10. `canteen_management/payments/models.py`
11. `canteen_management/payments/views.py`
12. `canteen_management/payments/management/commands/payment_consistency.py`

## 16. Short Project Summary

This project is now a role-based Django canteen system with:

- protected admin inventory management
- validated user registration
- responsive customer ordering UI
- atomic checkout
- explicit payment and receipt records
- integrity audit tooling
- coverage for the main bugs that were fixed during the recent cleanup work
