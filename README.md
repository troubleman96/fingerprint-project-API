# Secure Biometric Disciplinary API

Backend for a role-based student disciplinary and crime-history monitoring system for higher learning institutions. The architecture follows `backend_fingerprint.md`: DRF API, JWT authentication, role permissions, biometric enrollment/verification, disciplinary case workflow, reporting, and immutable audit logging.

## What This Backend Does

This API helps an institution:

- manage staff/admin/officer accounts;
- register students and departments;
- link students to fingerprint template hashes;
- verify a scanned fingerprint hash and identify the student;
- create and manage disciplinary cases;
- move cases through a controlled workflow;
- attach evidence documents and internal notes;
- show dashboard analytics;
- keep an audit trail of sensitive actions.

The backend does not talk directly to fingerprint scanner hardware. A local scanner SDK/agent should produce the fingerprint template/hash and send it to this API.

## Project Layout

```text
config/                 Django settings, root URLs, API route table
apps/accounts/          Users, JWT login, role definitions
apps/students/          Departments, student profiles, student search
apps/biometric/         Fingerprint template hashes and verification logs
apps/cases/             Disciplinary cases, notes, documents, workflow
apps/reports/           Dashboard statistics and future exports
apps/audit/             Immutable audit log and audit read API
utils/                  Shared response, pagination, exceptions, permissions
middleware/             Request mutation audit middleware
requirements/           Python dependencies by environment
backend_fingerprint.md  Original architecture/source-of-truth document
```

Each app has its own `README.md` with domain rules, models, endpoints, and common future changes.

## Setup

1. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements/development.txt
```

3. Create local environment file:

```bash
cp .env.example .env
```

4. Edit `.env` for your database. For quick local testing, you can remove `DATABASE_URL` and Django will use SQLite through the default in `config/settings/base.py`.

5. Run migrations after creating migration files:

```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create an admin:

```bash
python manage.py createsuperuser
```

7. Start the API:

```bash
python manage.py runserver
```

## API Documentation

When the server is running:

- Swagger UI: `http://localhost:8000/api/docs/`
- OpenAPI schema: `http://localhost:8000/api/schema/`
- Django admin: `http://localhost:8000/admin/`

## Standard Response Shape

Every API should return:

```json
{
  "success": true,
  "message": "Human readable message",
  "data": {},
  "errors": null,
  "meta": null
}
```

List endpoints put pagination in `meta`. Validation and auth errors are wrapped by `utils.exceptions.custom_exception_handler`.

## Authentication

JWT auth uses SimpleJWT.

Login:

```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "password"
}
```

Use the returned access token:

```http
Authorization: Bearer <access-token>
```

Refresh:

```http
POST /api/auth/refresh/
```

Current user:

```http
GET /api/auth/me/
```

## Role Model

Roles are defined in `apps/accounts/models.py`.

| Role | Main Responsibility |
|---|---|
| `ADMIN` | User management, all officer permissions, audit visibility |
| `OFFICER` | Student registration, biometric enrollment, case review, reports |
| `STAFF` | Filing reports and basic lookup flows |

Shared permissions live in `utils/permissions.py`.

## Main Endpoints

| Area | Endpoint |
|---|---|
| Login | `POST /api/auth/login/` |
| Refresh | `POST /api/auth/refresh/` |
| Current user | `GET /api/auth/me/` |
| Users | `GET/POST /api/users/`, `GET/PATCH/DELETE /api/users/<id>/` |
| Departments | `GET/POST /api/departments/` |
| Students | `GET/POST /api/students/`, `GET/PATCH/DELETE /api/students/<uuid>/` |
| Student cases | `GET /api/students/<uuid>/cases/` |
| Biometric enroll | `POST /api/biometric/enroll/` |
| Biometric verify | `POST /api/biometric/verify/` |
| Cases | `GET/POST /api/cases/`, `GET/PATCH/DELETE /api/cases/<uuid>/` |
| Case transition | `POST /api/cases/<uuid>/transition/` |
| Case notes | `GET/POST /api/cases/<uuid>/notes/` |
| Case documents | `GET/POST /api/cases/<uuid>/documents/` |
| Dashboard | `GET /api/reports/dashboard/` |
| Audit | `GET /api/audit/` |

## Case Workflow

Cases should move only through:

```text
REPORTED -> UNDER_REVIEW -> DECIDED -> CLOSED
```

Do not change `case.status` directly in views. Use:

```python
from apps.cases.services import transition_case_status
```

That service validates transitions and records decision fields when the case becomes `DECIDED`.

## Biometric Security Rule

The API stores only `template_hash`. It must never store raw fingerprint images.

Expected integration flow:

1. Scanner captures fingerprint locally.
2. Scanner SDK/local agent converts it to a template.
3. Agent hashes the template.
4. Frontend/API client sends the hash to `/api/biometric/enroll/` or `/api/biometric/verify/`.

## Audit Rules

`AuditLog` is append-only:

- model `save()` blocks updates once a row exists;
- model `delete()` always raises;
- mutating HTTP requests are logged by `middleware.audit_middleware.RequestAuditMiddleware`;
- sensitive manual actions should call `apps.audit.utils.log_action()`.

## How To Safely Make Changes

- Add new app URLs in `config/api_urls.py`.
- Keep API responses wrapped with `utils.response.api_response`.
- Put business rules in `services.py`, not directly inside serializers.
- Use string foreign keys for cross-app model references when possible.
- Avoid deleting users/students with real history; prefer soft-deactivation.
- Add app-specific documentation to that app’s `README.md` when behavior changes.

## Current Implementation Notes

This is a scaffold generated from `backend_fingerprint.md`. It includes models, serializers, views, permissions, settings, and docs, but migrations have not been generated yet. Run `python manage.py makemigrations` after installing dependencies.
