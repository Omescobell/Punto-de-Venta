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
  "id": 1,
  "first_name": "Maria",
  "last_name": "González",
  "phone_number": "5544332211",
  "email": "maria.gonzalez@email.com",
  "birth_date": "1995-08-20",
  "is_frequent": false
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
