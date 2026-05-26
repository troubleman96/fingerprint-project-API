# Accounts App

Owns authentication identities, JWT login behavior, and role definitions.

## Files

- `models.py`: `CustomUser`, `CustomUserManager`, `Role`
- `serializers.py`: JWT serializer plus read/write user serializers
- `views.py`: login, current user, admin user CRUD
- `admin.py`: Django admin registration

## Endpoints

| Method | Path | Purpose | Permission |
|---|---|---|---|
| `POST` | `/api/auth/login/` | Issue access/refresh JWTs | Public credentials check |
| `POST` | `/api/auth/refresh/` | Refresh access token | Valid refresh token |
| `GET` | `/api/auth/me/` | Current user profile | Authenticated |
| `GET` | `/api/users/` | List users | Admin |
| `POST` | `/api/users/` | Create user | Admin |
| `GET` | `/api/users/<id>/` | Read user | Admin |
| `PUT/PATCH` | `/api/users/<id>/` | Update user | Admin |
| `DELETE` | `/api/users/<id>/` | Soft deactivate user | Admin |

## Important Rules

- Email is the login field.
- Passwords must always be written through `set_password()` or `create_user()`.
- `DELETE /api/users/<id>/` does not remove the row. It sets `is_active=False` to preserve audit history.
- Role values are strings because they are easier to audit than numeric IDs.

## Common Changes

- Add a new role: update `Role`, `utils/permissions.py`, frontend role gates, and this README.
- Add fields to users: update `CustomUser`, serializers, admin, migrations, and API docs.
- Change JWT claims: edit `CustomTokenObtainPairSerializer.get_token()`.
