# Docugent – Authentication Guide

This document focuses on the authentication system: JWT tokens, login/registration flows, password changes, and protected access.

## What you get

- JWT authentication with access and refresh tokens
- Role-aware access via FastAPI dependencies (admin, moderator, user)
- Secure password hashing with per-user salt and failed-attempt tracking
- Token blacklist for logout/revocation


## Docker setup (recommended)

Run the auth-enabled backend with Docker. The entrypoint handles migrations and seeds roles/admin.

1. Create .env (minimum required)

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/db

# JWT
SECRET_KEY=your-256-bit-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Required app settings (placeholders ok for auth tests)
GOOGLE_API_KEY=dummy
GOOGLE_MAPS_API_KEY=dummy
GOOGLE_SHEETS_URL=https://example.com/sheet
CONFERENCE_VENUE_NAME=APIConf Venue
CONFERENCE_VENUE_ADDRESS=123 Example St
CONFERENCE_VENUE_COORDINATES=6.5244,3.3792
CONFERENCE_DATES=2025-09-01..2025-09-03
SUPPORT_PHONE=+1 555 0100
SUPPORT_EMAIL=support@example.com
```

2. Build and start

```bash
docker compose down -v && docker system prune -f && docker compose up --build
```

3. Verify

```bash
# Health check via NGINX (port 2025)
curl http://localhost:2025/api/v1/agents/health

# Example: get current user (requires Bearer token from login)
curl -H "Authorization: Bearer <access_token>" http://localhost:2025/api/v1/auth/me
```

Notes

- Backend Documentation is reachable at http://localhost:2025/docs via NGINX proxy.
- Migrations are auto-generated/applied on container start; default roles (admin, moderator, user) and the admin account are seeded if missing.
- Auth endpoints are under /api/v1/auth (register, login, refresh, logout, me, change-password).

Default admin (created by init script):

- Email: admin@apiconf.com
- Password: admin123!@# (change immediately)

## Data model (brief)

- users: public profile and role reference
- auth: one-to-one with users (hashed_password, salt, refresh_token, security fields)
- roles: admin, moderator, user (attached to users.role_id)
- token_blacklist: stores revoked tokens (token, type, user_id, expires_at)

### Data separation: public vs private

- The API returns only public user data (from the `users` table) via `UserResponse`: id, email, first_name, last_name, phone_number, is_active, is_verified, role, timestamps, and a computed full_name.
- Sensitive auth data (from the `auth` table) is never returned by the API. It contains hashed_password, salt, refresh_token(+expiry), and security fields (failed attempts, reset tokens).

## Password policy

- At least 8 characters
- Must include: one uppercase, one lowercase, and one digit

## JWT lifecycle

- Access token: short-lived (minutes)
- Refresh token: long-lived (days), stored in auth table
- Logout: refresh token blacklisted and cleared; access tokens are rejected if blacklisted

## RBAC and roles

- Default roles are seeded on first init: admin, moderator, user (see `scripts/init_db.py`).
- Role management endpoints exist under `/api/v1/roles` to perform CRUD. Create/Update/Delete require admin; reads are allowed per role guards.
- Access control helpers live in `app/dependencies/auth.py` (require_admin, require_moderator, require_user).

## Response envelope

All successful endpoints return:

```json
{
  "success": true,
  "data": {},
  "message": "..."
}
```

Errors use FastAPI HTTP errors (JSON with a "detail" message and proper status code).

## Endpoints (base path: /api/v1/auth)

### Register

- POST /register
- Body:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1 555 1234",
  "role_id": 1
}
```

- Response data (TokenResponse): access_token, refresh_token, token_type, expires_in, user

### Login

- POST /login
- Body:

```json
{ "email": "user@example.com", "password": "SecurePass123" }
```

- Response data (TokenResponse)

### Refresh access token

- POST /refresh
- Body:

```json
{ "refresh_token": "<refresh>" }
```

- Response data (TokenResponse)

### Logout

- POST /logout
- Auth: Bearer access token
- Body:

```json
{ "refresh_token": "<refresh>" }
```

- Effect: refresh token blacklisted and cleared

### Current user

- GET /me
- Auth: Bearer access token
- Response data: user

### Change password

- POST /change-password
- Auth: Bearer access token
- Body:

```json
{ "current_password": "OldPass123", "new_password": "NewPass123" }
```

- Effect: updates password, invalidates stored refresh token

## Deletion and revocation behavior

- Deleting a user cascades and deletes the corresponding row in `auth` (DB-level ON DELETE CASCADE).
- On logout, the current refresh token is cleared from the `auth` table and appended to `token_blacklist` (revoked). Access tokens remain valid until expiry unless explicitly blacklisted.

## Security notes

- Generate a strong SECRET_KEY (openssl rand -hex 32)
- Always use HTTPS in production
- Rotate secrets regularly and change default admin password after first login

## Implementation references

- Endpoints: app/api/v1/auth_router.py
- Schemas: app/schemas/auth.py (TokenResponse, UserRegistrationRequest, etc.)
- Dependencies: app/dependencies/auth.py (Bearer auth, role guards)
- Service: app/services/auth_service.py (hashing, JWTs, blacklist)
