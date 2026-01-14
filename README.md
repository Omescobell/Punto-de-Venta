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
  "username": "admin_user",
  "password": "secure_password"
}

Response (200 OK):
Note: The access token payload contains user_id, email, username, and role.

code
JSON
download
content_copy
expand_less
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
2. Refresh Token

Obtains a new access token using a valid refresh token.

Endpoint: /auth/refresh/

Method: POST

Access: Public

Request Body:

code
JSON
download
content_copy
expand_less
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
User Management
3. Get Current User Profile

Retrieves the profile information of the currently authenticated user.

Endpoint: /users/me/

Method: GET

Access: Authenticated

Response (200 OK):

code
JSON
download
content_copy
expand_less
{
  "id": 1,
  "username": "admin_user",
  "first_name": "Roberto",
  "last_name": "Gómez",
  "email": "roberto@enterprise.com",
  "phone_number": "555-0199",
  "address": "Main St 123",
  "role": "ADMIN",
  "is_active": true
}
4. Create User (Registration)

Registers a new user in the system.

Endpoint: /users/

Method: POST

Access: Public / Admin (Depending on permission settings)

Constraints:

email: Unique.

role: Must be one of ADMIN, EMPLOYEE, OWNER.

Request Body:

code
JSON
download
content_copy
expand_less
{
  "username": "employee_01",
  "email": "employee@enterprise.com",
  "password": "password123",
  "first_name": "Laura",
  "last_name": "Mendez",
  "phone_number": "555-9876",
  "address": "Second Ave 45",
  "role": "EMPLOYEE"
}
5. Update User Profile

Updates details of the currently authenticated user.

Endpoint: /users/me/

Method: PUT or PATCH

Access: Authenticated

Request Body:

code
JSON
download
content_copy
expand_less
{
  "first_name": "Laura Elena",
  "phone_number": "555-0000"
}
6. Delete User (Soft Delete)

Performs a logical deletion of the user. The record is preserved in the database but is_active is set to false.

Endpoint: /users/{id}/

Method: DELETE

Access: Admin / Authenticated

Response: 204 No Content

Session Management & Security
7. List Active Sessions

Retrieves a list of all active sessions (refresh tokens) associated with the current user. Useful for displaying connected devices (e.g., "Chatbot", "Chrome on Windows").

Endpoint: /sessions/

Method: GET

Access: Authenticated

Response (200 OK):

code
JSON
download
content_copy
expand_less
[
  {
    "id": 10,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
    "ip_address": "192.168.1.50",
    "created_at": "2023-10-27T10:00:00Z",
    "expires_at": "2023-11-03T10:00:00Z",
    "is_revoked": false
  }
]
8. Revoke Session

Forces a logout for a specific device by revoking its refresh token.

Endpoint: /sessions/{id}/revoke/

Method: POST

Access: Authenticated (Owner of the session)

Response (200 OK):

code
JSON
download
content_copy
expand_less
{
  "status": "Sesión cerrada correctamente"
}
Data Definitions
User Roles

The role field accepts the following enumerated string values:

Value	Description
ADMIN	System Administrator with full access.
EMPLOYEE	Standard user with access to POS functions.
OWNER	Business owner access level.
HTTP Status Codes

200 OK - Request succeeded.

201 Created - Resource successfully created.

204 No Content - Action succeeded (typically Delete) with no response body.

400 Bad Request - Invalid input data (e.g., duplicate email).

401 Unauthorized - Invalid or expired token.

403 Forbidden - User lacks permission for this resource.

404 Not Found - Resource does not exist.
