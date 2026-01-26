# API Documentation

## Overview
This API provides the backend services for the Point of Sale (POS) system and the Chatbot integration. It utilizes **JSON Web Tokens (JWT)** for stateless authentication, with an additional layer of session persistence to track user agents and IP addresses.

**Base URL:** `/api/` (configure according to environment)

---

## Authentication
The API uses Bearer Token authentication. Every request to protected endpoints must include the `Authorization` header.

**Header Format:**
`Authorization: Bearer <access_token>`

### 1. Login
Authenticates a user and establishes a session record. The system automatically captures the `User-Agent` and `IP Address` for security auditing.

*   **Endpoint:** `/auth/login/`
*   **Method:** `POST`
*   **Access:** Public

**Request Body:**
```json
{
  "email": "admin@enterprise.com",
  "password": "secure_password"
}
```
Response (200 OK):

Note: The access token payload contains user_id, email, username, and role.

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
### 2. Refresh Token

Obtains a new `access token` using a valid `refresh token`.

*  **Endpoint:** `/auth/refresh/`

*  **Method:** `POST`

* **Access:** Public

Request Body:

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```
## User Management

> **Security Notice:** Direct access to user management endpoints (Listing, Creating, Deleting) is strictly restricted to users with `ADMIN` or `OWNER` roles. `EMPLOYEE` accounts can only access the `/users/me/` endpoint.

### 3. Get Current User Profile
Retrieves the profile information of the currently authenticated user. This is the **only** user endpoint accessible to Employees.

**General Security Notes**
Field Visibility & Security:

       `Password`: Defined as `write_only`. It is required when creating a user but will never       appear in the API responses for security reasons.

       `Is Active`: Defined as `read_only`. This field is managed automatically by the system (e.g., via Soft Delete) and cannot be modified directly via PUT/PATCH.

*   **Endpoint:** `/users/me/`
*   **Method:** `GET`
*   **Access:** Authenticated (All Roles)

Description:
Retrieves a list of all active users in the system. Users marked as "inactive" (soft deleted) are excluded from this list.

**Response (200 OK):**
```json
{
  "id": 1,
  "username": "employee_juan",
  "role": "EMPLOYEE",
  ...
}
```
### 4. Create User (Registro)
Registers a new user in the system.

*   **Endpoint:** `/users/`
*   **Method:** `POST`
*   **Access:** **Restricted** (Requires `ADMIN` or `OWNER` role)

**Field Constraints:**

*   `email`: **Required & Unique.** Used as the login identifier.

*   `username`: **Required.**

*   `first_name`, `last_name`: **Required.**

*   `phone_number`: **Optional.** Accepts empty strings.

*   `address:` **Optional.** Accepts empty strings.

*   `role`: **Defaults** to `EMPLOYEE` if omitted.

**Request Body:**
```json
{
  "username": "employee_01",
  "email": "employee@enterprise.com",
  "password": "password123",    // Write Only (Input)
  "first_name": "Laura",
  "last_name": "Mendez",
  "phone_number": "555-9876",
  "address": "Second Ave 45",
  "role": "ADMIN"
}
```

**Request Body (Minimal Example - Optional fields omitted):**

```json
{
  "username": "cajero_juan",
  "email": "juan@enterprise.com",
  "password": "securePass123",
  "first_name": "Juan",
  "last_name": "Lopez"
  // phone_number and address are optional (blank=True)
}
```
**Response (201 Created):**

_Notice that `password` is NOT present in the response._

```json
{
  "id": 5,
  "username": "new_user",
  "email": "new@test.com",
  "first_name": "Juan",
  "last_name": "Perez",
  "role": "EMPLOYEE",
  "is_active": true
}
```
### 4.1. User Validation Errors (400 Bad Request)

Common error responses related to database constraints defined in the User model.

**Case A: Unique Email Constraint**
Since email is defined as unique=True and acts as the USERNAME_FIELD, attempting to register an email that is already taken will trigger this error.

```json
{
  "email": [
    "custom user with this email already exists."
  ]
}
```
**Case B: Required Fields Missing**
`first_name` and `last_name` do not have blank=True, so they cannot be empty.
{
  "first_name": [
    "This field is required."
  ],
  "password": [
    "This field is required."
  ]
}

### 5. Update User Profile

Updates details of the currently authenticated user.

* **Endpoint:** `/users/me/`

* **Method:** `PUT` or `PATCH`

* **Access:** Authenticated

Request Body:
```json
{
  "first_name": "Laura Elena",
  "phone_number": "555-0000"
}
```

### 6. Delete User (Soft Delete)

Performs a logical deletion of the user. The record is preserved in the database but is_active is set to false.

* **Endpoint:** `/users/{id}/`

* **Method:** `DELETE`

* **Access:** `Admin` / `Authenticated`

* **Response:** 204 No Content

## Session Management & Security
### 7. List Active Sessions

Retrieves a list of all active sessions (refresh tokens) associated with the current user. Useful for displaying connected devices (e.g., "Chatbot", "Chrome on Windows").

* **Endpoint:** `/sessions/`

* **Method:** `GET`

* **Access:** Authenticated

* **Response (200 OK):**

```json
  {
    "id": 10,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "ip_address": "192.168.1.50",
    "created_at": "2023-10-27T10:00:00Z",
    "expires_at": "2023-11-03T10:00:00Z",
    "is_revoked": false
  }
```

### 8. Revoke Session

Forces a logout for a specific device by revoking its refresh token.

* **Endpoint:** `/sessions/{id}/revoke/`

* **Method:** `POST`

* **Access:** Authenticated (`Owner` of the session)

* **Response (200 OK):**

```json
{
  "status": "Sesión cerrada correctamente"
}
```
## Supplier Management

Security Notice: Access to supplier resources (Listing, Creating, Updating, Deleting) is strictly restricted to users with ADMIN or OWNER roles. Employees do not have access to these endpoints.

### 9. List & Create Suppliers

Retrieves a list of all registered suppliers or creates a new one.

* **Endpoint:** `/suppliers/`

* **Methods:** `GET`, `POST`

* **Access:** Restricted (`ADMIN` or `OWNER`)

**Request Body (POST):**

```json
{
  "name": "Distribuidora de Bebidas S.A.",
  "mobile_number": "5512345678",
  "contact_person": "Carlos Rivera",
  "rfc": "DBE101010XYZ",
  "tax_address": "Av. Insurgentes Sur 123, CDMX"
}
```
* **Response** (`200 OK` - `LIST`):
```json
[
  {
    "id": 1,
    "name": "Distribuidora de Bebidas S.A.",
    "mobile_number": "5512345678",
    "contact_person": "Carlos Rivera",
    "rfc": "DBE101010XYZ",
    "tax_address": "Av. Insurgentes Sur 123, CDMX"
  },
  {
    "id": 2,
    "name": "Papelería Mayorista",
    ...
  }
]
```
### 10. Supplier Details (Retrieve, Update, Delete)

Operations on a specific supplier identified by its ID.

* **Endpoint:** `/suppliers/{id}/`

* **Methods:** `GET`, `PUT`, `PATCH`, `DELETE`
* **Access:** Restricted (`ADMIN` or `OWNER`)

**Request Body (`PUT`/`PATCH`):**
```json
{
  "contact_person": "Ana Torres",
  "mobile_number": "5598765432"
}
```
**Response (`204` No Content):**
* **Returned upon successful deletion (`DELETE`).**

## Customer Management

Allows authenticated users (including Employees) to register and manage customers for the POS system.
### 11. List & Create Customers

*   **Endpoint:** `/customers/`

*   **Methods:** `GET`, `POST`

*   **Access:** Authenticated (Any `Role`)

**Frequent Customer Status:** The `is_frequent` field is managed automatically by the system.

*   **Criteria:** A customer achieves "Frequent" status if they made at least one purchase in every   distinct calendar week of the previous month.

*   **Update Frequency:** This status is evaluated [AFTER A PURCHAE, ONLY ONCE A MONT].

**Request Body (`POST`):**

**Note:** is_frequent is read-only and defaults to false.
```json
{
  "first_name": "Maria",
  "last_name": "González",
  "phone_number": "5544332211",
  "email": "maria.gonzalez@email.com",
  "birth_date": "1995-08-20"
}
```
**Response (`201` Created):**
```json
{
  {
  "id": 1,
  "first_name": "Maria",
  "last_name": "González",
  "phone_number": "5544332211",
  "email": "maria.gonzalez@email.com",
  "birth_date": "1995-08-20",
  "is_frequent": false,
  "current_points": 0 //Default 0
  }
}
```
**Response (`200` OK):**

**Note**: current_points is read-only and calculated automatically based on transactions.
```json
{
  "id": 1,
  "first_name": "Maria",
  "last_name": "González",
  "phone_number": "5544332211",
  "email": "maria.gonzalez@email.com",
  "birth_date": "1995-08-20",
  "is_frequent": false,
  "current_points": 150 
}
```
### 12. Validation Errors (400 Bad Request)

The API enforces unique constraints and required fields. Below are the standard error responses for invalid inputs.

**Case A:** Duplicate Entry (Unique Constraints)
Occurs when trying to register a phone_number or email that already exists in the database.
```json
{
  "phone_number": [
    "customer with this phone number already exists."
  ],
  "email": [
    "customer with this email already exists."
  ]
}
```
**Case B:** Missing or Blank Fields
Occurs when required fields are omitted or sent as empty strings.

```json
{
  "first_name": [
    "This field is required."
  ],
  "birth_date": [
    "Date has wrong format. Use one of these formats instead: YYYY-MM-DD."
  ]
}
```
### 13. Customer Details

*   **Endpoint:** `/customers/{id}/`

*   **Methods:** `GET`, `PUT`, `PATCH`, `DELETE`

*   **Access:** Authenticated

**Request Body (`PATCH`):**
```json
{
  "email": "maria.nueva@email.com"
}
```
## Loyalty Points System

Endpoints dedicated to managing the customer's loyalty balance securely. Modifying current_points directly via the Customer Update endpoint is not possible; changes must be made through transactions.
### 14. Add or Redeem Points

Manually adds (EARN) or subtracts (REDEEM) points from a customer's balance. This creates a transaction record and updates the balance atomically.

*   **Endpoint:** `/customers/{id}/points/`

*   **Method:** `POST`

*   **Access:** `Authenticated`

#### Transaction Types:

*   **`EARN`**: Accumulate points from a purchase.

*   **`REDEEM`**: Spend points (Amount should be negative or handled by backend logic).

*   **`ADJUSTMENT`**: Manual correction.

**Request Body (`Earn` Points):**
```json
{
  "amount": 100,
  "transaction_type": "EARN",
  "description": "Purchase #1024 Bonus"
}
```
**Request Body (Redeem Points):**
```json
{
  "amount": -50,
  "transaction_type": "REDEEM",
  "description": "Discount applied"
}
```
**Response (201 Created):**
```json
{
  "status": "success",
  "new_balance": 200
}
```

### 15. Points History

Retrieves the full ledger of transactions for a specific customer, ordered by date (newest first).

*   **Endpoint:** `/customers/{id}/history/`

*   **Method:** `GET`

*   **Access:** Authenticated

**Response (200 OK):**
```json
[
  {
    "id": 10,
    "amount": -50,
    "transaction_type": "REDEEM",
    "description": "Discount applied",
    "created_at": "2023-10-27T14:30:00Z"
  },
  {
    "id": 9,
    "amount": 100,
    "transaction_type": "EARN",
    "description": "Purchase #1024 Bonus",
    "created_at": "2023-10-27T14:00:00Z"
  }
]
```

## Product Management

**Security Notice:**

*   **Employees:** Can `List`, `Create`, `Update`, and `Reserve` stock. They CANNOT `delete` products.

*   **Admins/Owners:** Have full access, including Delete.

### 16. List & Create Products

Retrieves the product catalog or registers a new item in the inventory.

*   **Endpoint:** `/products/`

*   **Methods:** `GET`, `POST`

*   **Access:** Authenticated (Any Role)

Request Body (POST):

*   **`sku`:** Unique. Stock Keeping Unit identifier.

*   **`supplier`:** ID of the registered supplier.
```json
{
  "name": "Coca Cola 600ml",
  "sku": "KO-600-MX",
  "price": 18.50,
  "current_stock": 100,
  "min_stock": 10,
  "supplier": 1
}
```
### 17. Product Details & Stock Reservation

Operations on a specific product. This includes the special endpoint to manage "Reserved Stock" atomically.

*   **Endpoint:** `/products/{id}/`

*   **Methods:** `GET`, `PUT`, `PATCH`, `DELETE` (`Admin` only)

### 17.1. Reserve or Release Stock

Used by the POS system when adding items to a cart (Reserve) or cancelling a cart (Release). Prevents race conditions.

*   **Endpoint:** `/products/{id}/reserve/`

*   **Method:** `POST`

*   **Access:** Authenticated (Employees Allowed)

**Logic:**

*   **Reserve (Add to cart):** Send a positive integer.

*   **Release (Remove from cart):** Send a negative integer.

**Scenario A: Reserve Stock (Add 5 items)**
```json
{
  "amount": 5
}
```
**Respone(200 OK):**
```json
{
  "status": "success",
  "product": "Coca Cola 600ml",
  "reserved_quantity": 5,
  "available_to_sell": 95
}
```
**Scenario B: Release Stock (Cancel 2 items)**

_Use a negative number to subtract from the reserved quantity._
```json
{
  "amount": -2
}
```
**Respone(200 OK):**
```json
{
  "status": "success",
  "product": "Coca Cola 600ml",
  "reserved_quantity": 3, //Updated total reserved
  "available_to_sell": 95
}
```

## Promotion Management

**Security Notice:**

*   **Employees:** Read-Only access (to apply discounts during sales).

*   **Admins/Owners:** Full access (Create/Edit/Delete).

### 18. List & Filter Promotions

To view promotions for a specific product, use the `?product={id}` query parameter.

*   **Endpoint:** `/promotions/?product={id}`

*   **Method:** `GET`

*   **Access:** Authenticated (Any Role)

**Example URL:** `/api/promotions/?product=15`

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Summer Sale",
    "description": "Valid for frequent customers only",
    "discount_percent": "15.00",
    "start_date": "2023-06-01",
    "end_date": "2023-06-30",
    "target_audience": "FREQUENT_ONLY",
    "is_active": true,
    "product": 15
  }
]
```
### 19. Create & Update Promotions

*   **Endpoint:** `/promotions/` (`Create`) or `/promotions/{id}/` (`Update`)

*   **Methods:** `POST`, `PUT`, `PATCH`, `DELETE`

*   **Access:** Restricted (`ADMIN` or `OWNER`)

**Request Body (POST):**

_Note: product `ID` is required in the body._
```json
{
  "name": "Black Friday",
  "description": "50% off on electronics",
  "product": 15,
  "discount_percent": 50.00,
  "start_date": "2023-11-24",
  "end_date": "2023-11-26",
  "target_audience": "ALL"
}
```
### Error Handling & Validations

Common validation errors specific to the Products and Promotions modules.

**Case A: Duplicate SKU (Product)**

The `sku` field must be unique across the entire database.

**Status:** `400 Bad Request`
```json
{
  "sku": [
    "product with this sku already exists."
  ]
}
```
**Case B: Invalid Dates (Promotion)**

The `start_date` cannot be later than the `end_date`. This validation runs on both Create (`POST`) and Update (`PATCH`).

**Status:** `400 Bad Request`
```json
{
  "end_date": [
    "La fecha de finalización debe ser posterior a la fecha de inicio."
  ]
}
```
**Case C: Insufficient Stock (Reservation)**

Occurs when trying to reserve more items than physically available (`current_stock`).

**Status:** `400 Bad Request`
```json
{
  "error": "Insufficient stock.",
  "available": 2
}
```
**Case D: Invalid Release (Reservation)**

Occurs when trying to release (negative amount) more items than are currently reserved.

**Status:** `400 Bad Request`

```json
{
  "error": "Cannot release more items than reserved."
}
```

**Case E: Permission Denied (Delete/Promotions)**

Occurs when an Employee tries to delete a product or modify a promotion.

**Status:** `403 Forbidden`

```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Order Management (Point of Sale)

This module handles the core transactional logic. It uses Atomic Transactions to ensure data integrity: if any part of the sale fails (e.g., insufficient stock for one item), the entire order is rolled back.

**Key Features:**

*   **Inventory sync:** Automatically deducts `current_stock` and clears `reserved_quantity`.

*   **Loyalty Integration:** Calculates points (1% of total) and updates the customer's level.

*   **Price Snapshot:** Stores the `unit_price` at the moment of sale, preventing historical data changes if catalog prices are updated later.

*   **Birthday Logic:** Automatically detects if today is the customer's birthday and apply 10% discount.

### 20. List & Create Orders

Retrieves the sales history or processes a new sale.

*   **Endpoint:** `/orders/`

*   **Methods:** `GET`, `POST`

*   **Access:** Authenticated (All Roles - Employees are allowed to sell)

**Request Body (POST - New Sale):**

*   **`customer`:** Optional. `ID` of the registered customer. If omitted, the sale is treated as "Anonymous".

*   **`items`:** Required. List of products to purchase.

*   **`promotion_id`:** Optional. ID of a specific promotion to apply to a line item.

```json
{
  "customer": 1, 
  "payment_method": "CASH",
  "items": [
    {
      "product_id": 15,
      "quantity": 2,
      "promotion_id": 5
    },
    {
      "product_id": 20,
      "quantity": 1
      // No promotion applied
    }
  ]
}
```
**Response (201 Created):**

_Note: The `total`, `ticket_folio`, and `discount_amount` are calculated automatically by the backend. `The product_id` is REQUIRED_
```json
{
  "id": 102,
  "ticket_folio": "F47AC10B",
  "created_at": "2023-10-27T15:30:00Z",
  "payment_method": "CASH",
  "status": "PAID",
  "seller_name": "employee_juan",
  "money_saved_total": 20.00,          
  "discount_applied": 0.07,            
  "is_birthday_discount_applied": true,
  "customer": 1,
  "customer_name": "Maria González",
  "total": "270.50",
  "final_ammount" : "250.50"
  "items": [
    {
      "product_id": 15, - REQUIRED
      "quantity": 2,
      "product_name": "Coca Cola 600ml",
      "unit_price": "100.00",
      "promotion_name": "Summer Sale",
      "discount_amount": "20.00",
      "subtotal": "180.00"
    },
    {
      "product_id": 20,
      "quantity": 1,
      "product_name": "Chips",
      "unit_price": "70.50",
      "promotion_name": null,
      "discount_amount": "0.00",
      "subtotal": "70.50"
    }
  ]
}
```

### 21. Order Details & Management

Retrieves full details of a specific ticket.

**Security Notice:** While Employees can create orders, Updates and Deletions are strictly restricted to `ADMIN` or `OWNER`roles to prevent fraud (e.g., modifying a ticket after payment).

*   **Endpoint:** `/orders/{id}/`

*   **Methods:** `GET`, `PUT`, `PATCH`, `DELETE`

*   **Access:

       *   **`GET`:** Authenticated (All Roles)

       *   **`PUT`/`PATCH`/`DELETE`:** Restricted (`ADMIN` or `OWNER`)

**Response (200 OK):**

Returns the same structure as the "Create Order" response.

### 22. Order Validation Errors (400 Bad Request)

The API performs strict validation on stock levels and business rules before processing any payment.

**Case A:** Insufficient Stock Occurs when the requested quantity exceeds the `current_stock` available in the database. The entire transaction is rejected.
```json
{
  "non_field_errors": [
    "Stock insuficiente para Producto Test. Disponible: 5"
  ]
}
```
**Case B:** Empty Order Occurs when the items list is empty or missing.
```json
{
  "items": [
    "No se puede crear una orden sin productos."
  ]
}
```
**Case C:** Invalid Quantity Quantities must be positive integers greater than zero.
```json
{
  "items": [
    {
      "quantity": [
        "La cantidad debe ser al menos 1."
      ]
    }
  ]
}
```
**Case D:** Integrity Errors Occurs if the provided product_id or customer ID does not exist.
```json
{
  "items": [
    {
      "product_id": [
        "Invalid pk \"9999\" - object does not exist."
      ]
    }
  ]
}
```
### Business Logic Notes (Internal Guide)

**Promotions:**

*   The system validates that the promotion is active, within the date range, and matches the product.

*   If target_audience is set to FREQUENT_ONLY, the discount will be silently ignored (set to 0.00) if the customer is not a frequent buyer or if the sale is anonymous.

**Loyalty Points:**

*   Points are calculated as 1% of the total purchase, rounded to the nearest integer.

*   Points are only assigned if a customer is linked to the order.

**Data Snapshots:**

*   The system saves a copy of product_name and unit_price in the OrderItems table. Future changes to the Product Catalog (e.g., price increases) will not affect historical sales records.
## Data Definitions
### User Roles

The role field accepts the following enumerated string values:

| Value        |Description                                     |
|--------------|------------                                    |
| ADMINS       |System `Administrator` with full access.        |
| EMPLOYEE	   |Standard user with access to `POS` functions.   |
| OWNER	       |Business owner access level.                    |

## HTTP Status Codes 
* 200 OK - Request succeeded.

* 201 Created - Resource successfully created.

* 204 No Content - Action succeeded (typically Delete) with no response body.

* 400 Bad Request - Invalid input data (e.g., duplicate email).

* 401 Unauthorized - Invalid or expired token.

* 403 Forbidden - User lacks permission for this resource.

* 404 Not Found - Resource does not exist.
