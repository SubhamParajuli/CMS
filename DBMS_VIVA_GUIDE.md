# DBMS Viva Guide

Updated: 2026-03-12
Course: DBMS BCT III_I
Project: Django-based Canteen Management System using PostgreSQL in production

This guide is written as a viva-preparation and defense document. It maps the implemented project design to core DBMS syllabus concepts using the actual models, relationships, transactions, and deployment architecture present in the codebase.

## 1. Project Context for Viva

Your project is a transactional Canteen Management System with the following core business areas:

- user and role management through `accounts.CustomUser`
- menu item and stock management through `inventory.Inventory`
- order placement through `orders.Order` and `orders.OrderItem`
- payment and receipt tracking through `payments.Payment` and `payments.Receipt`

From a DBMS perspective, this is a relational database application with:

- master-detail design for orders and order items
- one-to-many and one-to-one relationships
- integrity constraints
- transaction management during checkout
- concurrency protection for stock updates
- production deployment on PostgreSQL

## 2. Chapter 2: Data Models and ER Mapping

### 2.1 Relational Data Model Used in the Project

The project is implemented using Django ORM, but the underlying database structure is relational.

Each model maps to a table:

- `CustomUser` -> user table
- `Inventory` -> menu items table
- `Order` -> orders table
- `OrderItem` -> order details table
- `Payment` -> payments table
- `Receipt` -> receipts table

### 2.2 Main Entities

#### CustomUser

Attributes:

- `id`
- `username`
- `password`
- `email` inherited through Django auth structure
- `user_code`
- `role`

Primary role in the system:

- identifies who is placing an order or managing the canteen

#### Inventory

Attributes:

- `id`
- `item_name`
- `category`
- `price`
- `quantity`
- `food_image`
- `is_available`

Primary role in the system:

- stores each food item that can be sold

#### Order

Attributes:

- `id`
- `user_id`
- `order_date`
- `total_amount`
- `is_paid`

Primary role in the system:

- stores one complete purchase transaction

#### OrderItem

Attributes:

- `id`
- `order_id`
- `item_id`
- `quantity`
- `price_at_purchase`

Primary role in the system:

- stores each line item inside an order

#### Payment

Attributes:

- `id`
- `order_id`
- `payment_method`
- `amount_paid`
- `payment_time`

Primary role in the system:

- stores payment data for a paid order

#### Receipt

Attributes:

- `id`
- `order_id`
- `generated_at`

Primary role in the system:

- stores receipt generation metadata for the order

### 2.3 Primary Keys and Foreign Keys

#### Primary Keys

All major tables use Django's default integer primary key `id`.

Examples:

- `CustomUser.id`
- `Inventory.id`
- `Order.id`
- `OrderItem.id`
- `Payment.id`
- `Receipt.id`

#### Foreign Keys

The project uses these real foreign-key relationships:

- `Order.user -> CustomUser`
- `OrderItem.order -> Order`
- `OrderItem.item -> Inventory`

The project also uses one-to-one references, which are functionally specialized foreign keys with uniqueness:

- `Payment.order -> Order`
- `Receipt.order -> Order`

### 2.4 Cardinalities in the Actual Project

#### One-to-Many

`CustomUser` to `Order`

- one user can place many orders
- each order belongs to exactly one user

`Order` to `OrderItem`

- one order can contain many line items
- each line item belongs to exactly one order

`Inventory` to `OrderItem`

- one inventory item can appear in many order-item records
- each order-item record refers to exactly one inventory item

#### One-to-One

`Order` to `Payment`

- one paid order should have only one payment record

`Order` to `Receipt`

- one paid order should have only one receipt record

#### Many-to-Many

There is no direct many-to-many field declared in the models, but conceptually the relationship between `Order` and `Inventory` is many-to-many and is resolved through the associative entity `OrderItem`.

A strong examination point here is the distinction between conceptual and implemented many-to-many design.

A concise oral explanation is:

- one order contains many inventory items
- one inventory item can appear in many different orders
- therefore the true conceptual relationship is many-to-many
- this is implemented relationally through `OrderItem`

### 2.5 ER Model Explanation

You can describe the ER design as follows:

- `CustomUser` is an entity
- `Inventory` is an entity
- `Order` is an entity
- `OrderItem` is a weak or associative entity joining orders and inventory items
- `Payment` and `Receipt` are dependent entities linked to an order

If you are asked to draw or explain the ER diagram, the mapping is:

- `CustomUser` 1 --- N `Order`
- `Order` 1 --- N `OrderItem`
- `Inventory` 1 --- N `OrderItem`
- `Order` 1 --- 1 `Payment`
- `Order` 1 --- 1 `Receipt`

## 3. Chapter 3: SQL, ORM, Joins, Aggregation, and Views

### 3.1 Mapping Django ORM to SQL Categories

#### DDL: Data Definition Language

DDL means schema definition operations such as:

- `CREATE TABLE`
- `ALTER TABLE`
- `DROP TABLE`

In your project, DDL is primarily generated through Django migrations.

Examples from your codebase:

- creating `Inventory`, `Order`, `OrderItem`, `Payment`, and `Receipt` tables
- altering `Inventory.quantity` to a `PositiveIntegerField`
- adding the `related_name='orders'` improvement on `Order.user`
- creating constraints on `accounts.CustomUser.role`

In an oral defense, a precise answer is:

"I usually write models in Django ORM, and Django migrations translate those model changes into SQL DDL statements."

#### DML: Data Manipulation Language

DML means inserting, updating, deleting, and selecting data.

Examples from your real application:

- admin adds a new inventory item
- admin updates item quantity or price
- admin deletes an inventory item
- checkout inserts rows into `Order`, `OrderItem`, `Payment`, and `Receipt`
- checkout updates inventory stock and item availability

Django ORM examples from your code:

- `Inventory.objects.create(...)`
- `Order.objects.create(...)`
- `OrderItem.objects.create(...)`
- `inventory_item.save(update_fields=[...])`
- `Inventory.objects.filter(...)`

#### DCL: Data Control Language

DCL mainly refers to access control commands like:

- `GRANT`
- `REVOKE`

In this Django project, application-level access control is handled by:

- authentication
- `login_required`
- custom `admin_required`
- user roles in `CustomUser.role`

Strictly speaking, that is application-layer authorization rather than raw SQL DCL. In PostgreSQL administration, DCL would be managed through database roles and user privileges if needed.

### 3.2 How Joins Work in Your Project

Your analytics and order pages rely on relational joins, even though Django ORM writes them indirectly.

#### Example: Order to User Join

When you use:

```python
Order.objects.select_related('user')
```

Django performs a SQL join between orders and users so the username can be fetched efficiently.

#### Example: OrderItem to Inventory Join

When admin order views display item names inside each order, Django resolves:

- `OrderItem.order`
- `OrderItem.item`

This is equivalent to joining order-item rows with inventory rows.

#### Example: Analytics Join Path

Your analytics queries use:

- `OrderItem.objects.filter(order__is_paid=True, order__order_date__gte=start_date)`
- `.values('item__item_name', 'item__category')`
- `.annotate(quantity_sold=Sum('quantity'), order_count=Count('order', distinct=True))`

This means:

- join `OrderItem` with `Order`
- join `OrderItem` with `Inventory`
- group the rows by item name and category
- aggregate quantities and counts

### 3.3 GROUP BY and HAVING in Your Analytics

#### GROUP BY

Your sales analytics conceptually uses `GROUP BY` when you summarize sales per item or per user.

Example from your analytics logic:

- weekly best sellers
- monthly best sellers
- top customers of the month

Equivalent SQL-style thinking:

```sql
SELECT i.item_name, SUM(oi.quantity) AS quantity_sold
FROM orders_orderitem oi
JOIN inventory_inventory i ON oi.item_id = i.id
JOIN orders_order o ON oi.order_id = o.id
WHERE o.is_paid = TRUE
GROUP BY i.item_name;
```

#### HAVING

You do not explicitly write a `HAVING` clause in the current code, but the concept applies if you want to filter grouped results after aggregation.

Example relevant to your project:

- show only food items sold more than 20 times this month
- show only customers with more than 5 paid orders

Equivalent SQL example:

```sql
SELECT u.username, COUNT(o.id) AS order_count
FROM orders_order o
JOIN accounts_customuser u ON o.user_id = u.id
WHERE o.is_paid = TRUE
GROUP BY u.username
HAVING COUNT(o.id) > 5;
```

### 3.4 Theoretical Use of Database Views

Your current code does not create a PostgreSQL database view directly, but a database view would be very appropriate for reporting.

#### Example view for daily canteen sales summary

Conceptually, you could create a view such as:

- total paid orders per day
- total revenue per day
- total items sold per day

Example conceptual SQL:

```sql
CREATE VIEW daily_sales_summary AS
SELECT
    DATE(order_date) AS sales_day,
    COUNT(id) AS paid_orders,
    SUM(total_amount) AS total_revenue
FROM orders_order
WHERE is_paid = TRUE
GROUP BY DATE(order_date);
```

Why this is useful in your project:

- analytics page could read from a summarized view instead of recalculating the same aggregate repeatedly
- reporting becomes cleaner for admin dashboards
- viva answer becomes stronger because you connect theory with a practical reporting use case

## 4. Chapter 4: Normalization and Constraints

### 4.1 Domain and Integrity Constraints in Your Code

Your project already enforces several constraints.

#### Domain constraints

- `role` must be one of `admin`, `student`, or `teacher`
- `user_code` must be exactly 5 digits
- `price` must be positive
- `quantity` must be non-negative
- `payment_method` is constrained by application logic

#### Entity integrity

- every main table has a primary key
- primary keys are unique and non-null

#### Referential integrity

- an `Order` cannot exist without a valid `CustomUser`
- an `OrderItem` must refer to a valid `Order`
- an `OrderItem` must refer to a valid `Inventory` item
- a `Payment` and `Receipt` must refer to a valid `Order`

### 4.2 First Normal Form (1NF)

1NF requires atomic values and no repeating groups.

Your schema satisfies 1NF because:

- each column stores a single value
- one inventory item is stored per row
- one order item is stored per row
- quantities are atomic integer values
- categories are stored as single values, not comma-separated lists

For example, the system does not store multiple ordered items inside one `Order` column. Instead, each ordered item is stored separately in `OrderItem`.

### 4.3 Second Normal Form (2NF)

2NF requires 1NF plus full dependency on the whole key.

Your design satisfies 2NF because:

- `OrderItem` separates line-item details from the order header
- fields like `quantity` and `price_at_purchase` belong to a specific order-item row
- non-key attributes are not partially dependent on only part of a composite business meaning

Even though Django uses surrogate primary keys, the business meaning of `OrderItem` still depends on the combination of order and item participation.

### 4.4 Third Normal Form (3NF)

3NF requires that non-key attributes do not depend on other non-key attributes.

Your schema satisfies 3NF because:

- user role and user code are stored in `CustomUser`, not copied into every order
- item name, category, and current price are stored in `Inventory`, not duplicated in unrelated master tables
- `Order` stores order-level facts such as total amount and paid status
- `OrderItem` stores line-level facts such as purchased quantity and purchase-time price
- payment information is separated into `Payment`
- receipt metadata is separated into `Receipt`

This design reduces update anomalies and redundancy.

### 4.5 BCNF

BCNF requires that every determinant is a candidate key.

For viva, you can argue that the schema is close to BCNF because:

- primary-key attributes determine the row data
- one-to-one tables such as `Payment` and `Receipt` use unique links to `Order`
- important business constraints are kept in the correct owning relation

There is no evidence in your schema of storing one fact in multiple places unnecessarily across accounts, inventory, and orders.

### 4.6 Why `price_at_purchase` Is Correct and Not Redundancy

An examiner may challenge the existence of both:

- current `Inventory.price`
- historical `OrderItem.price_at_purchase`

A defensible answer is:

"That is intentional and necessary. `Inventory.price` stores the current menu price, while `OrderItem.price_at_purchase` preserves the historical transaction price so old receipts remain correct even if the menu price changes later."

This is good normalization for transactional systems.

## 5. Chapter 6: Indexing and Hashing

### 5.1 PostgreSQL Indexing in This Project

PostgreSQL commonly uses B+ Tree indexes by default for primary keys, unique keys, and many lookup operations.

In your project, B+ Tree indexing is relevant for:

- primary keys such as `id`
- unique fields such as `CustomUser.user_code`
- foreign-key columns such as `Order.user_id`, `OrderItem.order_id`, and `OrderItem.item_id`

Why this helps:

- faster record lookup by primary key
- faster joins between related tables
- faster filtering of user orders and item-based order details

### 5.2 Foreign-Key Query Optimization

Your code frequently performs relational access such as:

- selecting orders with their users
- selecting order items with their inventory items
- filtering paid orders by date

These patterns benefit from indexes because PostgreSQL can locate matching rows more efficiently during joins and filtering.

### 5.3 Hashing Concepts

Static and dynamic hashing are syllabus concepts more often discussed theoretically than used directly in Django code.

#### Static hashing

- fixed number of buckets
- simpler but less flexible as data grows

#### Dynamic hashing

- bucket structure can expand as data grows
- more adaptable for large or changing datasets

In PostgreSQL, hash-based access methods exist, but most of your common project queries are better explained through B+ Tree indexing because they involve:

- equality lookups
- range filtering by date
- sorted results
- join operations

For viva, the strongest answer is:

"In my project, practical performance benefits mainly come from PostgreSQL's B+ Tree indexes on keys and foreign keys. Hashing is a valid DBMS concept for exact-match lookup, but my real workload also needs joins, sorting, and date filtering, so B+ Tree indexing is more central."

## 6. Chapter 7: Concurrency and ACID

### 6.1 ACID Properties in Your Checkout Flow

Your checkout flow is an excellent example of ACID.

#### Atomicity

Either all checkout operations succeed or none do.

In your code, checkout performs:

1. cart validation
2. stock validation
3. order creation
4. order-item creation
5. stock deduction
6. payment creation
7. receipt creation
8. marking the order as paid

Because these operations are inside `transaction.atomic()`, partial success is prevented.

#### Consistency

The database moves from one valid state to another.

Examples from your project:

- quantity cannot go negative if validation fails
- unavailable items cannot be sold
- payment and receipt are created for a paid order

#### Isolation

Concurrent transactions should not corrupt one another.

Your project improves isolation using:

- `select_for_update()` on inventory rows during checkout

This prevents simultaneous writes from overselling the same stock.

#### Durability

Once a successful transaction commits, the data remains stored even if the server crashes afterward.

This durability is guaranteed by PostgreSQL's transaction and logging system.

### 6.2 Last Momo Plate Example

Suppose two students try to order the last plate of Momo at the same time.

What happens in your project?

1. Both requests reach the checkout view.
2. PostgreSQL locks the matching inventory row when `select_for_update()` is used.
3. The first transaction that gets the lock validates quantity and updates stock.
4. The second transaction waits.
5. After the first transaction commits, the second transaction reads the updated quantity.
6. If stock is now zero, the second transaction gets a validation error such as `Only 0 left` or item unavailable.

This is exactly why PostgreSQL is better than SQLite for production concurrency.

### 6.3 MVCC in PostgreSQL

PostgreSQL uses MVCC, which stands for Multi-Version Concurrency Control.

Main idea:

- readers do not always block writers
- writers do not always block readers
- multiple transaction versions are managed safely

For oral explanation, a concise answer is:

"PostgreSQL keeps multiple row versions so concurrent operations can proceed more safely. In my checkout logic I still use row-level locking with `select_for_update()` for stock rows, because stock deduction is a critical write operation."

## 7. Chapter 8: Crash Recovery and WAL

### 7.1 Crash During Checkout

Suppose the server crashes during checkout after the order is created but before the payment and receipt are created.

Without transaction control, that would leave inconsistent data.

In your system, the transaction is atomic, so if the crash occurs before commit:

- PostgreSQL rolls back the uncommitted transaction
- incomplete order changes are not permanently stored
- inventory stock is not left half-updated

### 7.2 Write-Ahead Logging

PostgreSQL uses Write-Ahead Logging, abbreviated as WAL.

Core principle:

- changes are first recorded in the log
- then applied to the database pages

Why this matters:

- supports crash recovery
- ensures committed transactions can be recovered
- helps preserve atomicity and durability

### 7.3 Log-Based Recovery in Your Project Context

In your project, WAL protects operations such as:

- stock deduction
- order insertion
- payment insertion
- receipt insertion
- order status update to paid

If the crash happens before commit:

- transaction is rolled back

If the crash happens after commit:

- WAL helps PostgreSQL restore the committed changes during recovery

## 8. PostgreSQL vs SQLite for Viva Defense

You should be ready for this question because your project uses both.

### SQLite in your project

Advantages:

- easy local setup
- no external database server required
- useful for quick development and testing

Limitations:

- weaker write concurrency
- not ideal for multiple real users placing orders simultaneously
- file-based architecture is less suitable for Railway production

### PostgreSQL in your project

Advantages:

- production-grade concurrency control
- MVCC support
- better transaction management
- stronger reliability under multi-user workload
- more appropriate for hosted deployment and live ordering

A strong answer in examination language is:

"I kept SQLite for fast local development and test convenience, but Railway production uses PostgreSQL because my application contains concurrent stock updates and transactional checkout, which require stronger multi-user database guarantees."

## 9. Likely Viva Questions and Model Answers

### 1. Why did you create a separate `OrderItem` table?

Answer:

I separated `OrderItem` because one order can contain many menu items and one inventory item can appear in many different orders. That is a many-to-many relationship conceptually, so `OrderItem` works as the associative table and also stores line-specific data such as purchased quantity and purchase-time price.

### 2. Why do you store both `Inventory.price` and `OrderItem.price_at_purchase`?

Answer:

`Inventory.price` stores the current selling price, while `OrderItem.price_at_purchase` preserves the historical transaction amount. If the admin changes the menu price later, old orders and receipts must still show the original purchase price.

### 3. What normalization forms does your database satisfy?

Answer:

The schema satisfies 1NF because values are atomic, 2NF because line-item facts are stored in a separate order-detail table, and 3NF because user, inventory, order, payment, and receipt facts are kept in their proper tables instead of being redundantly copied. It is also close to BCNF because determinants are mainly keys or unique references.

### 4. How is concurrency handled if two students order the same last item simultaneously?

Answer:

The checkout code uses `transaction.atomic()` and `select_for_update()` on inventory rows. PostgreSQL locks the stock row for the first transaction. The second transaction waits and then sees the updated quantity, preventing overselling.

### 5. Why is PostgreSQL better than SQLite for your production deployment?

Answer:

PostgreSQL is better for multi-user production because it supports stronger concurrency control, MVCC, better transaction handling, and a proper server-based architecture. SQLite is fine for local development, but not ideal for concurrent live ordering.

### 6. Where are joins used in your project?

Answer:

Joins are used when loading orders with users, when showing order items with inventory item names, and when computing analytics such as best-selling items and top customers. Django ORM expresses these joins through `select_related`, related lookups, and aggregation queries.

### 7. What is the role of `transaction.atomic()` in your project?

Answer:

It makes checkout a single transaction. If any step fails, such as payment creation or stock validation, the entire checkout is rolled back so the database never stores a half-complete order.

### 8. What is a database view, and how could it help your project?

Answer:

A database view is a virtual table produced by a query. In my project, a view could be used to store a daily sales summary for reporting, such as number of paid orders and total revenue per day, which would simplify analytics queries.

### 9. What integrity constraints are enforced in your project?

Answer:

The project enforces primary keys, foreign keys, unique user codes, valid user roles, non-negative quantities, positive prices, and authenticated access rules. These constraints protect both database consistency and application correctness.

### 10. How does PostgreSQL recover after a crash?

Answer:

PostgreSQL uses Write-Ahead Logging. Changes are logged before they are fully applied to the data pages. After a crash, PostgreSQL uses the log to recover committed transactions and roll back incomplete ones.

## 10. Short Viva Closing Statement

If the examiner asks for a final summary, an appropriate closing answer is:

"My project is a relational DBMS application built with Django ORM. It uses normalized entities for users, inventory, orders, payments, and receipts. The checkout flow is transaction-safe, production runs on PostgreSQL, concurrency is protected through row locking and MVCC, and the schema supports both operational processing and admin analytics."
