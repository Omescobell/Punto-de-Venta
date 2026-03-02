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
  "phone_number": "5512345678",
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
    "phone_number": "5512345678",
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
  "phone_number": "5598765432"
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

## Store Credit Management

This module manages the internal credit line for Frequent Customers. It allows viewing the transaction history and registering payments to reduce debt.

### 16. Credit Transaction History

Retrieves the complete financial ledger for a specific customer, including charges (purchases), payments, and manual adjustments.

*   **Endpoint:** `/customers/{id}/credit-history/`

*   **Method:** `GET`

*   **Access:** Authenticated

**Response (200 OK):**

Returns a list ordered by date (newest first).

```json
[
  {
    "id": 45,
    "amount": "200.00",
    "transaction_type": "PAYMENT",
    "description": "Cash payment at register",
    "created_at": "2023-10-28T10:00:00Z"
  },
  {
    "id": 44,
    "amount": "550.50",
    "transaction_type": "CHARGE",
    "description": "Purchase - Ticket #F-902",
    "created_at": "2023-10-27T16:30:00Z"
  }
]
```

### 17. Pay Off Credit (Register Payment)

Registers a payment towards the customer's debt. This action reduces the credit_used balance and immediately releases available_credit.

*   **Endpoint:** `/customers/{id}/pay-credit/`

*   **Method:** `POST`

*   **Access:** Authenticated

**Business Rules:**

*   **Positive Amount:** The payment amount must be greater than zero.

*   **Idempotency:** Paying more than the current debt will result in a credit_used balance of 0.00 (it does not create a negative balance/store credit surplus in this version).

**Request Body:**
```json
{
  "amount": 200.00,
  "description": "Partial payment via Bank Transfer"
}
```
**Response (200 OK):**

Returns the updated balance status immediately after the transaction.

```json
{
  "status": "success",
  "new_credit_used": "350.50",
  "available_credit": "1649.50"
}
```

### 18. Credit Logic & Errors (400 Bad Request)

The API enforces logic defined in the model. Below are standard error responses for credit operations.

**Case A: Invalid Amount**

Occurs when trying to pay a negative amount or sending an empty value.
```json
{
  "error": [
    "El monto del abono debe ser positivo." 
  ]
}
```
**Case B: Insufficient Credit (On Purchase/Charge)**
*Note: Charges usually happen via the Order endpoint, but this logic applies.*
{
  "error": [
    "Crédito insuficiente. Disponible: $50.00"
  ]
}



## Product Management

**Security Notice:**

*   **Employees:** Can `List`, `Create`, `Update`, and `Reserve` stock. They CANNOT `delete` products.

*   **Admins/Owners:** Have full access, including Delete.

**Features**

*   **Low Stock**: The system automatically updates the `low_stock` field. 

### 16. List & Create Products

Retrieves the product catalog or registers a new item in the inventory.

*   **Endpoint:** `/products/`

*   **Methods:** `GET`, `POST`

*   **Access:** Authenticated (Any Role)

**Tax Calculation Logic:** The backend automatically calculates `final_price` based on the `tax_rate` provided.

*   `final_price` = `price` + (`price` * `tax_rate`)

*   **Note:** `final_price` is Read-Only. If sent in the request, it will be ignored.

**Supported Tax Rates (`tax_rate`):**

*   `"16.00"`: IVA General (16%)

*   `"8.00"`: IVA Fronterizo (8%)

*   `"0.00"`: Tasa Cero (0%)

*   `"EXENT"`: Exento.

Request Body (POST):

*   **`sku`:** Unique. Stock Keeping Unit identifier.

*   **`supplier`:** ID of the registered supplier.
```json
{
  "name": "Coca Cola 600ml",
  "sku": "KO-600-MX",
  "price": "18.50",       // Base price
  "tax_rate": "0.16",     // 16% IVA
  "current_stock": 100,
  "supplier": 1
}
```
**Response (201 Created):**
```json
{
  "id": 10,
  "name": "Coca Cola 600ml",
  "sku": "KO-600-MX",
  "price": "18.50",
  "tax_rate": "0.16",
  "final_price": "21.46",  //(18.50 + 16%)
  "current_stock": 100,
  "reserved_quantity": 0,
  "available_to_sell": 100,
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
**Automatic Logic (Backend):** When a promotion is created or its date arrives:

*   The system automatically updates the target Product's discounted_price field.

*   The Product's `final_price` is automatically recalculated (Tax is applied to the new discounted price).

*   When the promotion expires, the price automatically reverts to normal.

**Target audience(`target_audience`):**

*   `"ALL"`: ALL CUSTOMERS

*   `"FREQUENT_ONLY"`: FREQUENT ONLY CUSTOMERS

**Request Body (POST):**

_Note: product `ID` is required in the body._
```json
{
  "name": "Black Friday",
  "description": "50% off on electronics",
  "product": 15,
  "discount_percent": 50.00, // The system will do the math
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

**Case F: Overlapping Promotions (Promotion)** Trying to create a promotion when one already exists for that product in that timeframe.

**Status:** `400 Bad Request`
```json
{
  "non_field_errors": [
    "Ya existe una promoción activa para este producto en las fechas seleccionadas (2024-01-01 a 2024-01-05)."
  ]
}
```
## Order Management (Point of Sale)

This module handles the core transactional logic of the system. It is designed to be the "Single Source of Truth" for all financial calculations.

**Technical Integration Notes (Read before implementing Frontend):**

*   **Do NOT Calculate Totals on Client:** The Backend automatically calculates Subtotals, VAT (16%), Discounts (Birthday/Promotions), and Final Totals. The Frontend should only display the values returned by the API.

*   **Stock Reservation:** Stock is deducted immediately upon Creating the order (Status: `PENDING`), not when paying. This prevents "overselling" while the client decides how to pay.

*   **Atomic Transactions:** All endpoints use database atomicity. If a payment fails (e.g., insufficient points), the entire transaction rolls back.

*   **Snapshots:** The `unit_price` is saved at the moment of creation. Changing the product price in the catalog later will not affect existing orders.

**Data Definitions**

**1. Order Status Lifecycle**

The order flow is strictly unidirectional to ensure audit integrity.

| Status | Description | Transitions Allowed |
|--------|-------------|---------------------|
|`Pending`|Default state. Stock is reserved. Waiting for payment.|→ `PAID` or `CANCELLED`
|`PAID`|Sale completed. Financials recorded. Points awarded.|**Final State** (Cannot be cancelled)|
|`CANCELLED`|Sale aborted. Stock restored to inventory.|**Final State**|

**2. Payment Methods**

The `payment_method` field triggers specific backend validations:

| Code | Logic Triggered |
|------|-----------------|
|`CASH`| Standard processing. |
|`CARD`| Standard processing (External terminal auth assumed). |
|`POINTS`| Validation: Checks if `customer.loyalty_points >= total`. Deducts points. |
|`CREDIT`| Validation: Checks if `(current_debt + total) <= credit_limit`. Increases debt. |

### 20. Create Order (Draft)

Initializes a sale. This endpoint reserves stock and performs all tax/discount calculations.

*   **Endpoint:** `/orders/`

*   **Method:** `POST`

*   **Auth:** Authenticated User

Request Body:

*   `customer`: (Optional) Integer ID. If omitted, sale is "Anonymous".

*   `items`: (Required) List of objects with `product_id` and `quantity`.

```json
{
  "customer": 1,
  "items": [
    {
      "product_id": 15,
      "quantity": 2
    },
    {
      "product_id": 20,
      "quantity": 1
    }
  ]
}
```
**Response (201 Created):** Returns the order in `PENDING` status with full financial breakdown.

```json
{
  "id": 102,
  "ticket_folio": "F47AC10B",
  "status": "PENDING",
  "created_at": "2023-10-27T15:30:00Z",
  "customer": 1,
  "customer_name": "Maria González",
  "subtotal": "200.00",           // Sum of items before tax
  "total_tax": "32.00",           // Total IVA (16%)
  "final_amount": "232.00",       // Total to be paid
  "money_saved_total": "10.00",   // Sum of all discounts
  "items": [
    {
      "product_id": 15,
      "product_name": "Coca Cola 600ml",
      "quantity": 2,
      "unit_price": "86.21",      // Base Price (Tax exclusive)
      "tax_amount": "27.58",
      "discount_amount": "10.00", 
      "amount": "172.42"          // Line Subtotal
    }
  ]
}
```

### 21. Process Payment

Finalizes the transaction. This confirms the sale and triggers loyalty point accrual or credit debt updates.

*   **Endpoint:** `/orders/{id}/pay/`

*   **Method:** `POST`

**Request Body:**
```json
{
  "payment_method": "CREDIT" // Options: "CASH", "CARD", "POINTS", "CREDIT"
}
```
Response (200 OK): Updates status to PAID.
```json
{
  "id": 102,
  "status": "PAID",
  "payment_method": "CREDIT",
  "paid_at": "2023-10-27T15:35:00Z",
  "final_amount": "232.00"
}
```
### 22. Cancel Order (Void)

Cancels a `PENDING` order. This is the "Undo" function. It automatically releases the reserved stock back to the global inventory.

*   **Endpoint:** `/orders/{id}/cancel/`

*   **Method:** `POST`

*   **Constraint:** Cannot cancel an order if status is already `PAID`.

**Request Body: (Empty JSON object allowed)**
```json
{}
```
**Response (200 OK):**
```json
{
  "status": "Order cancelled",
  "detail": "La orden 102 fue cancelada y el stock restaurado."
}
```

### 23. Error Handling (400 Bad Request)

The frontend should listen for these specific error structures to show user-friendly alerts.

**Case A:** Insufficient Stock (On Create) The user tries to buy more items than available.

```json
{
  "non_field_errors": [
    "Stock insuficiente para 'Coca Cola'. Disponible: 5, Solicitado: 10"
  ]
}
```
**Case B: Credit Limit Exceeded (On Pay)** *The customer tries to pay with CREDIT but has reached their limit.*
```json
{
  "detail": "El cliente excede su límite de crédito. Límite: 1000.00, Saldo actual: 950.00, Compra: 200.00"
}
```
**Case C: Insufficient Points (On Pay)** *The customer tries to pay with POINTS but has low balance.*
```json
{
  "detail": "Saldo de puntos insuficiente. Puntos disponibles: 50.00, Total a pagar: 120.00"
}
```
**Case D: Invalid Cancellation (On Cancel)** *User tries to cancel a paid order.*
```json
{
  "non_field_errors": [
    "No se puede cancelar esta orden. Solo se permiten cancelar órdenes PENDIENTES."
  ]
}
```
### Business Logic Notes (Internal Guide)

**Loyalty Points:**

*   Points are calculated as 1% of the total purchase, rounded to the nearest integer.

*   Points are only assigned if a customer is linked to the order.

## ChatBot User Management

**Security Notice:**

*  **Employees:** No Access (Requests return 403 Forbidden).

*  **Admins/Owners:** Full access (Create/Read/Update/Delete).

### 24. List & Retrieve Users

To view all registered Telegram users or retrieve details for a specific user by their mobile number.

*   **Endpoint:** `api/chatbotusers/` (List) or `/chatbotusers/{mobile_number}/` (Detail)

*   **Method:** `GET`

*   **Access:** Restricted (`ADMIN` or `OWNER`)

    **Example URL:** `/api/chatbotusers/+521234567890/`

**Response (200 OK):**

```json
{
  "mobile_number": "+521234567890",
  "name": "Juan Perez",
  "last_interaction": "2023-10-27T10:30:00Z"
}
```
### 25. Create & Update Users

*   **Endpoint:** `/chatbotusers/` (Create) or `/chatbotusers/{mobile_number}/` (Update)

*   **Methods:** `POST`, `PATCH`, `DELETE`

*   **Access:** Restricted (`ADMIN` or `OWNER`)

**Request Body (`POST`):** Note: `mobile_number` serves as the Primary Key and must be unique.

```json
{
  "mobile_number": "+521234567890",
  "name": "Juan Perez"
}
```
**Request Body (PATCH):** Note:`last_interaction` is read-only and cannot be modified manually.
```json
{
  "name": "Juan Updated"
}
```
### Error Handling & Validations

Common validation errors specific to the ChatBot Users module.

**Case A:** Permission Denied Occurs when a user with the Employee role attempts to access any endpoint in this module. Status: 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```
**Case B:** Duplicate Mobile Number The `mobile_number` field acts as the Primary Key and must be unique. Status: 400 Bad Request
```json
{
  "mobile_number": [
    "chat bot users with this mobile number already exists."
  ]
}
```
**Case C:** Invalid Mobile Number Format Occurs if the provided number exceeds the character limit. Status: 400 Bad Request
```json
{
  "mobile_number": [
    "Ensure this field has no more than 20 characters."
  ]
}
```
**Case D:** Resource Not Found Occurs when trying to access a specific user that does not exist in the database. Status: 404 Not Found
```json
{
  "detail": "Not found."
}
```

## Analytics

**Security Notice:**

*   **Employees:** CANNOT access any endpoints in this module. Attempting to do so will return a `403 Forbidden`.

*   **Admins/Owners:** Have full access to view business metrics and reports.

**Features**

*   **Strict Date Validation:** The system automatically validates if the requested date range has existing records. If no sales exist on the requested dates, it halts the process to save database resources and suggests the valid operational dates.

*   **Paid Orders Only:** All financial metrics strictly exclude `PENDING` or `CANCELED` orders to guarantee accounting accuracy.

### 26. Sales Summary

Generates a comprehensive financial and operational report for a specific period. It aggregates total revenue, calculates average tickets, identifies the peak hours of operation, and groups revenue by payment methods.

*   **Endpoint:** `/analytics/sales-summary/`

*   **Methods:** `GET`

*   **Access:** Authenticated (`Admin` & `Owner` Only)

Query Parameters (Optional):

*   `start_date` (YYYY-MM-DD): Start of the analysis period.

*   `end_date` (YYYY-MM-DD): End of the analysis period.

*   *Note*: If no dates are provided, the system defaults to the last 30 days of operation.

**Response (200 OK):**
```json
{
  "analyzed_period": {
    "start_date": "2023-10-01",
    "end_date": "2023-10-31"
  },
  "general_summary": {
    "total_revenue": 2494.00,
    "average_ticket": 831.33,
    "lowest_ticket": 116.00,
    "highest_ticket": 1218.00,
    "total_tickets": 3
  },
  "products": {
    "total_units_sold": 5,
    "top_product": {
      "product_name": "Laptop",
      "revenue": 2000.00
    },
    "breakdown": [
      {
        "product_name": "Laptop",
        "units_sold": 2,
        "revenue": 2000.00
      },
      {
        "product_name": "Mouse",
        "units_sold": 3,
        "revenue": 150.00
      }
    ]
  },
  "peak_hours": {
    "most_profitable_hour": {
      "hour": 14,
      "total_revenue": 1334.00,
      "ticket_count": 2
    },
    "busiest_hour": {
      "hour": 14,
      "total_revenue": 1334.00,
      "ticket_count": 2
    },
    "hourly_breakdown": [
      {
        "hour": 10,
        "total_revenue": 1160.00,
        "ticket_count": 1
      },
      {
        "hour": 14,
        "total_revenue": 1334.00,
        "ticket_count": 2
      }
    ]
  },
  "payment_methods": [
    {
      "payment_method": "CARD",
      "total_sales": 2,
      "average_ticket": 1189.00,
      "highest_ticket": 1218.00,
      "accumulated_amount": 2378.00
    },
    {
      "payment_method": "CASH",
      "total_sales": 1,
      "average_ticket": 116.00,
      "highest_ticket": 116.00,
      "accumulated_amount": 116.00
    }
  ]
}
```
**Scenario A: Invalid Dates or No Records (400 Bad Request)**

Occurs if the user requests a date in the future, a date where the store was closed, or sends a malformed string.

```json
{
  "error": "No sales found for the date 2024-12-31 in the system.",
  "first_system_record": "2023-01-15",
  "last_system_record": "2023-10-31"
}
```
### 27. Product Sales Ranking

Returns a ranked list of the most or least sold products based purely on units sold (inventory movement), not revenue.

*   **Endpoint:** `/analytics/product-ranking/`, example `/api/analytics/product-ranking/?limit=5&criterion=most`

*   **Methods:** `GET`

*   **Access:** Authenticated (`Admin` & `Owner` Only)

**Query Parameters (Optional):**

*   `start_date` (YYYY-MM-DD): Start of the analysis period.

*    `end_date` (YYYY-MM-DD): End of the analysis period.

*    `limit` (Integer): Number of results to return per list. Default is `10`.

*    `criterion` (String): Accepts `"most"`, `"least"`, or `"both"`. Default is `"most"`.

**Response (200 OK) - Using `criterion=ambos` and `limit=2`:**
```json
{
  "analyzed_period": {
    "start_date": "2023-10-01",
    "end_date": "2023-10-31"
  },
  "results": {
    "criterion": "both",
    "results_limit": 2,
    "most_sold": [
      {
        "product__id": 3,
        "product_name": "Teclado",
        "units_sold": 5,
        "revenue": 750.00
      },
      {
        "product__id": 2,
        "product_name": "Mouse",
        "units_sold": 3,
        "revenue": 150.00
      }
    ],
    "least_sold": [
      {
        "product__id": 1,
        "product_name": "Laptop",
        "units_sold": 1,
        "revenue": 1000.00
      },
      {
        "product__id": 2,
        "product_name": "Mouse",
        "units_sold": 3,
        "revenue": 150.00
      }
    ]
  }
}
```
**Scenario A: Valid Dates, but No Items Sold (200 OK)**

Occurs when the dates are valid system dates, but specifically, no items were sold (e.g., store was open but no sales were made).
```json
{
  "analyzed_period": {
    "start_date": "2023-10-01",
    "end_date": "2023-10-01"
  },
  "detail": "No products sold in the selected period."
}
```

### 28. Low Stock Report

Identifies products with low inventory levels. If a custom threshold is not provided, it defaults to returning products that are automatically flagged by the system (`low_stock=True`).

*   **Endpoint:** `/analytics/reports/low-stock/`, example `/api/analytics/reports/low-stock/?threshold=10`

*   **Methods:** `GET`

*   **Access:** Authenticated (`Admin` & `Owner` Only)

**Query Parameters (Optional):**

*   `threshold` (Integer): A custom quantity. The system will return all products where current_stock is less than or equal to this number.

**Response (200 OK - Results Found):**

Returns an array of products ordered from highest to lowest stock within the threshold.
```json
[
  {
    "name": "Coca Cola 600ml",
    "current_stock": 8
  },
  {
    "name": "Galletas Emperador",
    "current_stock": 2
  },
  {
    "name": "Agua Ciel 1L",
    "current_stock": 0
  }
]
```
**Scenario A: Invalid Threshold or No Products in Threshold (200 OK)**

Occurs when there are no products matching the criteria, the system is empty, or the user inputs an invalid threshold format (e.g., text instead of a number).

```json
{
  "message": "No hay productos dentro del umbral establecido."
}
```

### 29. Dead Inventory Report

Identifies "dead" inventory: products that have not generated any paid sales since a specified reference date. This is crucial for clearing out non-moving stock.

*   **Endpoint:** `/analytics/reports/dead-inventory/`, example `/api/analytics/reports/dead-inventory/?reference_date=2023-10-01`

*   **Methods:** `GET`

*   **Access:** Authenticated (`Admin` & `Owner` Only)

**Query Parameters (Optional):**

*   `reference_date` (YYYY-MM-DD): The date to start searching for sales.

*   *Note:* If no date is provided, the system defaults to analyzing the last 30 days of operation.

**Response (200 OK - Results Found):**

Returns an array of the dead products, including their ID to easily link them to the product management module.
```json
[
  {
    "id": 14,
    "name": "Funda iPhone 12 Rosa",
    "current_stock": 15
  },
  {
    "id": 42,
    "name": "Cargador Genérico USB-C",
    "current_stock": 50
  }
]
```

**Scenario A: All Products Sold or Invalid Date (200 OK)**

Occurs if every single product in the catalog has had at least one sale in the requested period, or if the user sends an invalid date string.
```json
{
  "message": "Todos los productos han tenido ventas en este período."
}
```

### 30. Customer Sales History

Retrieves the complete sales history and behavior metrics for a specific customer within a given timeframe.

*   **Endpoint:** `/analytics/customer-sales/`, example `/api/analytics/customer-sales/?customer_id=5&start_date=2023-10-01`

*   **Methods:** `GET`

*   **Access:** Authenticated (`Admin` & `Owner` Only)

**Query Parameters:**

*   `customer_id` (Integer) **Required:** The unique identifier of the customer.

*   `start_date` (YYYY-MM-DD) **Optional:** Start of the analysis period.

*   `end_date` (YYYY-MM-DD) **Optional:** End of the analysis period. Defaults to the last 30 days.

**Response (200 OK - Results Found):**
```json
{
  "customer_info": {
    "id": 5,
    "name": "Juan Pérez",
    "email": "juan.perez@email.com"
  },
  "analyzed_period": {
    "start_date": "2023-10-01",
    "end_date": "2023-10-31"
  },
  "sales_metrics": {
    "total_spent": 1500.00,
    "average_ticket": 500.00,
    "total_tickets": 3
  },
  "top_product": {
    "product_name": "Laptop",
    "total_spent_on_product": 1000.00,
    "units_bought": 1
  },
  "peak_buying_hours": [
    {
      "hour": 18,
      "total_spent": 1000.00,
      "ticket_count": 1
    },
    {
      "hour": 10,
      "total_spent": 500.00,
      "ticket_count": 2
    }
  ],
  "payment_methods": [
    {
      "payment_method": "CARD",
      "total_sales": 2,
      "average_ticket": 250.00,
      "accumulated_amount": 500.00
    },
    {
      "payment_method": "CASH",
      "total_sales": 1,
      "average_ticket": 1000.00,
      "accumulated_amount": 1000.00
    }
  ]
}
```
**Scenario A: Customer Validated, but No Purchases in Period (200 OK)**
```json
{
  "customer_info": {
    "id": 5,
    "name": "Juan Pérez"
  },
  "analyzed_period": {
    "start_date": "2023-10-01",
    "end_date": "2023-10-31"
  },
  "detail": "This customer made no purchases during the selected period."
}
```
**Scenario B: Customer Does Not Exist (404 Not Found)**
```json
{
  "error": "Customer not registered in the system."
}
```

### 31. Sales Velocity & Depletion Estimation

Calculates the daily sales velocity (sell-through rate) of a specific product and estimates the number of days until its inventory is depleted based on that rate. Automatically adjusts the analysis period if the product's first sale occurred more recently than the requested timeframe.

*   **Endpoint:** `/analytics/sales-velocity/`, example `/api/analytics/sales-velocity/?identifier=FAST123&period_days=30`

*   **Methods:** `GET`

*   **Access:** Authenticated (`Admin` & `Owner` Only)

**Query Parameters:**

*   **`identifier` (String) Required:** The exact `name` or barcode (`SKU`) of the product (case-insensitive).

*   **`period_days` (Integer) Optional:** The number of historical days to analyze. Defaults to 30.

**Response (200 OK - Results Found):**
```json
{
  "product_name": "Laptop Gamer",
  "product_sku": "FAST123",
  "analyzed_period_days": 30,
  "total_units_sold": 60,
  "sales_velocity": 2.0,
  "current_stock": 100,
  "depletion_estimation_days": 50
}
```
**Scenario A: Product Validated, but No Sales in Period (200 OK)**
```json
{
  "product_name": "Mouse Viejo",
  "product_sku": "SLOW123",
  "analyzed_period_days": 30,
  "total_units_sold": 0,
  "sales_velocity": 0.0,
  "current_stock": 50,
  "depletion_estimation_days": "Indefinida"
}
```
**Scenario B: Missing Identifier (400 Bad Request)**
```json
{
  "error": "Product identifier (Name or SKU) is required."
}
```
**Scenario C: Product Does Not Exist (404 Not Found)**
```json
{
  "error": "Product not found in the system."
}
```

### 31. Inventory Valuation & Financial Metrics

Calculates the total financial value of the current inventory based on the provider cost (price) and the retail price with tax (`final_price`). Projects potential profit and profit margins for the entire inventory or a specific product.

*   **Endpoint:** `/api/analytics/inventory-valuation/`, example, SKU `/api/analytics/inventory-valuation/?product_identifier=TEC001`, name `/api/analytics/inventory-valuation/?product_identifier=Monitor%20Gamer`

*   **Methods:** `GET`

    Access: Authenticated (Admin & Owner Only)

Query Parameters:

*   `product_identifier` (String) Optional: The exact `name` or barcode (`SKU`) of a specific product to evaluate. *(Note: If not provided, the system evaluates the Entire Inventory).*

**Response (200 OK - Results Found):**
```json
{
  "scope": "Entire Inventory",
  "financial_metrics": {
    "total_inventory_cost": 150.00,
    "total_potential_sale": 174.00,
    "total_potential_profit": 24.00,
    "profit_margin_percentage": 13.79
  }
}
```
**Scenario A: Specific Product Validated (200 OK)**
```json
{
  "scope": "Specific Product: TEC001",
  "financial_metrics": {
    "total_inventory_cost": 50.00,
    "total_potential_sale": 58.00,
    "total_potential_profit": 8.00,
    "profit_margin_percentage": 13.79
  }
}
```
**Scenario B: Product Validated but No Stock / Not Found (404 Not Found)**
```json
{
  "error": "No products available in the selected scope."
}
```

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
