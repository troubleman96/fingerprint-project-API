# Frontend API Usage Guide

## Base Configuration

- **Base URL:** `/api/`
- **Auth Type:** JWT (Bearer Token)
- **Auth Header:** `Authorization: Bearer <access_token>`
- **Access Token Lifetime:** 8 hours
- **Refresh Token Lifetime:** 7 days
- **Default Page Size:** 25 (max 100)

---

## Standard Response Envelope

Every endpoint returns this shape:

```json
{
  "success": true,
  "message": "string",
  "data": {},
  "errors": null,
  "meta": {
    "total": 100,
    "page": 1,
    "page_size": 25,
    "total_pages": 4,
    "has_next": true,
    "has_previous": false
  }
}
```

`meta` is only present on list endpoints. `errors` is only present on validation failures.

---

## Role-Based Access

| Role | Access Level |
|------|-------------|
| `ADMIN` | Full access — user management + all officer permissions |
| `OFFICER` | Student registration, biometric enrollment, case management, reports, audit |
| `STAFF` | File reports, student/case lookup, biometric verification |

The JWT token carries custom claims: `role`, `full_name`, `email`. Read them from the decoded token to drive UI role checks.

---

## Authentication

### POST `/api/auth/login/`
No auth required.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secret"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "full_name": "Jane Doe",
      "role": "OFFICER",
      "department": "Academic Affairs",
      "phone": "+256700000000",
      "is_active": true
    }
  }
}
```

---

### POST `/api/auth/refresh/`
No auth required.

**Request:**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "access": "<new_jwt_access_token>"
  }
}
```

---

### GET `/api/auth/me/`
Returns the currently authenticated user's profile.

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "role": "OFFICER",
    "department": "Academic Affairs",
    "phone": "+256700000000",
    "is_active": true
  }
}
```

---

## Users
> ADMIN only

### GET `/api/users/`
**Query params:** `page`, `page_size`, `search` (email/full_name), `ordering`

**Response data array:**
```json
{
  "id": 1,
  "email": "string",
  "full_name": "string",
  "role": "ADMIN|OFFICER|STAFF",
  "department": "string | null",
  "phone": "string | null",
  "is_active": true
}
```

---

### POST `/api/users/`
**Request:**
```json
{
  "email": "string (required)",
  "full_name": "string (required)",
  "role": "ADMIN|OFFICER|STAFF (required)",
  "password": "string (required, min 8 chars)",
  "department": "string (optional)",
  "phone": "string (optional)",
  "is_active": true
}
```

**Response (201):** User object (same shape as list item above).

---

### GET `/api/users/{id}/`
**Response (200):** Single user object.

---

### PATCH `/api/users/{id}/`
Send only the fields you want to change.

**Response (200):** Updated user object.

---

### DELETE `/api/users/{id}/`
Soft-deactivates the user (`is_active = false`). Does not hard-delete.

**Response (200):**
```json
{ "success": true, "message": "User deactivated" }
```

---

## Departments
> ADMIN or OFFICER

### GET `/api/departments/`
**Query params:** `page`, `page_size`, `search` (name/code), `ordering`

**Response data array:**
```json
{
  "id": 1,
  "name": "Computer Science",
  "code": "CSC"
}
```

---

### POST `/api/departments/`
```json
{
  "name": "string (required, unique)",
  "code": "string (required, unique)"
}
```
**Response (201):** Department object.

---

### GET `/api/departments/{id}/`
**Response (200):** Single department object.

---

### PATCH `/api/departments/{id}/`
**Response (200):** Updated department object.

---

### DELETE `/api/departments/{id}/`
**Response (204):** No content.

---

## Students
> All roles (ADMIN / OFFICER / STAFF)

### GET `/api/students/`
**Query params:**

| Param | Type | Description |
|---|---|---|
| `page` | integer | Page number |
| `page_size` | integer | Items per page (max 100) |
| `search` | string | Searches reg_number, first_name, last_name, email |
| `ordering` | string | `last_name`, `reg_number`, `created_at` (prefix `-` for DESC) |
| `department` | integer | Filter by department ID |
| `biometric_enrolled` | boolean | `true` or `false` |
| `academic_year` | string | e.g. `2024/2025` |
| `is_active` | boolean | `true` or `false` |

**Response data array (list view):**
```json
{
  "id": "uuid",
  "reg_number": "CSC/2024/001",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "department_name": "Computer Science",
  "academic_year": "2024/2025",
  "biometric_enrolled": false,
  "is_active": true,
  "case_count": 2
}
```

---

### POST `/api/students/`
Use `multipart/form-data` if uploading a photo, otherwise `application/json`.

**Request:**
```json
{
  "reg_number": "string (required, unique)",
  "first_name": "string (required)",
  "last_name": "string (required)",
  "department_id": 1,
  "academic_year": "2024/2025 (required)",
  "date_of_birth": "YYYY-MM-DD (optional)",
  "gender": "M|F|O (optional)",
  "level": "string (optional)",
  "phone": "string (optional)",
  "email": "string (optional)",
  "photo": "file (optional)"
}
```

**Response (201) — full detail object:**
```json
{
  "id": "uuid",
  "reg_number": "CSC/2024/001",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "date_of_birth": "2001-05-20",
  "gender": "M",
  "department": { "id": 1, "name": "Computer Science", "code": "CSC" },
  "academic_year": "2024/2025",
  "level": "Year 2",
  "phone": "+256700000000",
  "email": "john@example.com",
  "photo": "/media/students/photo.jpg",
  "biometric_enrolled": false,
  "is_active": true,
  "registered_by": "Jane Doe",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

### GET `/api/students/{uuid}/`
**Response (200):** Full student detail object (same as POST response).

---

### PATCH `/api/students/{uuid}/`
Send only changed fields. Supports `multipart/form-data` for photo updates.

**Response (200):** Full student detail object.

---

### DELETE `/api/students/{uuid}/`
Soft-deactivates (`is_active = false`).

**Response (200):**
```json
{ "success": true, "message": "Student deactivated" }
```

---

### GET `/api/students/{uuid}/cases/`
Returns all disciplinary cases for this student.

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "case_number": "DIT-2024-0001",
      "incident_type_name": "Academic Misconduct",
      "severity": "HIGH",
      "status": "UNDER_REVIEW",
      "outcome": null,
      "date_of_incident": "2024-01-10",
      "location": "Exam Hall A",
      "created_at": "2024-01-11T08:00:00Z"
    }
  ]
}
```

---

## Biometric

### POST `/api/biometric/enroll/`
> ADMIN or OFFICER only

Enrols a student's fingerprint template.

**Request:**
```json
{
  "reg_number": "CSC/2024/001 (required)",
  "template_hash": "64-char hex string (required)",
  "finger_used": "right_index (optional, default: right_index)",
  "quality_score": 0.95
}
```

`template_hash` must match regex `^[a-fA-F0-9]{64}$` — it represents a SHA256-equivalent hash of the biometric template captured by the scanner.

**Response (200):**
```json
{ "success": true, "message": "Student biometric enrolled successfully" }
```

---

### POST `/api/biometric/verify/`
> All roles

Looks up a student by their fingerprint hash.

**Request:**
```json
{
  "template_hash": "64-char hex string (required)",
  "workstation_id": "string (optional)"
}
```

**Response (200) — match found:**
```json
{
  "success": true,
  "message": "Biometric verified",
  "data": {
    "student_id": "uuid",
    "reg_number": "CSC/2024/001",
    "full_name": "John Doe",
    "department": "Computer Science"
  }
}
```

**Response (401) — no match:**
```json
{ "success": false, "message": "Fingerprint not recognised" }
```

---

## Disciplinary Cases
> List/detail: ADMIN or OFFICER. Create: all roles.

### GET `/api/cases/`
**Query params:**

| Param | Type | Description |
|---|---|---|
| `page` | integer | Page number |
| `page_size` | integer | Items per page (max 100) |
| `search` | string | case_number, student reg/last_name, description |
| `ordering` | string | `date_of_incident`, `created_at`, `status`, `severity` |
| `student` | uuid | Filter by student UUID |
| `incident_type` | integer | Filter by incident type ID |
| `status` | string | `REPORTED\|UNDER_REVIEW\|DECIDED\|CLOSED` |
| `severity` | string | `LOW\|MEDIUM\|HIGH` |
| `date_from` | date | Incidents on or after (YYYY-MM-DD) |
| `date_to` | date | Incidents on or before (YYYY-MM-DD) |

**Response data array (list view):**
```json
{
  "id": "uuid",
  "case_number": "DIT-2024-0001",
  "student": { "id": "uuid", "reg_number": "...", "full_name": "...", "department_name": "..." },
  "incident_type_name": "Academic Misconduct",
  "severity": "HIGH",
  "status": "UNDER_REVIEW",
  "outcome": null,
  "date_of_incident": "2024-01-10",
  "location": "Exam Hall A",
  "created_at": "2024-01-11T08:00:00Z"
}
```

---

### POST `/api/cases/`
> All roles

**Request:**
```json
{
  "student": "uuid (required)",
  "incident_type": 1,
  "severity": "HIGH",
  "description": "string (required)",
  "date_of_incident": "YYYY-MM-DD (required)",
  "location": "string (optional)",
  "assigned_to": 3
}
```

**Response (201):** Full case detail object (see GET `/{uuid}/` below).

---

### GET `/api/cases/{uuid}/`
> ADMIN or OFFICER

**Response (200) — full detail:**
```json
{
  "id": "uuid",
  "case_number": "DIT-2024-0001",
  "student": { "id": "uuid", "reg_number": "...", "full_name": "...", "department_name": "..." },
  "incident_type": { "id": 1, "name": "Academic Misconduct", "severity_default": "HIGH", "is_active": true },
  "severity": "HIGH",
  "status": "UNDER_REVIEW",
  "outcome": null,
  "outcome_notes": null,
  "description": "Caught with notes during exam",
  "date_of_incident": "2024-01-10",
  "location": "Exam Hall A",
  "reported_by": "Jane Doe",
  "assigned_to": "John Smith",
  "decided_by": null,
  "decided_at": null,
  "notes": [
    {
      "id": 1,
      "body": "Student denies involvement",
      "created_by": 2,
      "created_by_name": "Jane Doe",
      "created_at": "2024-01-12T09:00:00Z"
    }
  ],
  "documents": [
    {
      "id": 1,
      "file": "/media/cases/evidence.pdf",
      "original_filename": "evidence.pdf",
      "description": "Exam scan",
      "uploaded_by": 2,
      "uploaded_by_name": "Jane Doe",
      "uploaded_at": "2024-01-12T09:05:00Z"
    }
  ],
  "created_at": "2024-01-11T08:00:00Z",
  "updated_at": "2024-01-12T09:05:00Z"
}
```

---

### PATCH `/api/cases/{uuid}/`
> ADMIN or OFFICER

Send only changed fields.

**Response (200):** Full case detail object.

---

### DELETE `/api/cases/{uuid}/`
> ADMIN or OFFICER

**Response (204):** No content.

---

### POST `/api/cases/{uuid}/transition/`
> ADMIN or OFFICER

Moves a case through its workflow. Transitions are strictly enforced.

**Allowed transitions:**
- `REPORTED` → `UNDER_REVIEW`
- `UNDER_REVIEW` → `DECIDED` (must supply `outcome`)
- `DECIDED` → `CLOSED`

**Request:**
```json
{
  "status": "DECIDED (required)",
  "outcome": "CLEARED|WARNING|SUSPENSION|EXPULSION|REFERRED (required when moving to DECIDED)",
  "outcome_notes": "string (optional)"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Case status updated to DECIDED",
  "data": { "full case detail object" }
}
```

**Response (400) — invalid transition:**
```json
{ "success": false, "errors": { "status": ["Invalid transition from REPORTED to CLOSED"] } }
```

---

### GET `/api/cases/{uuid}/notes/`
> ADMIN or OFFICER

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "body": "Student denies involvement",
      "created_by": 2,
      "created_by_name": "Jane Doe",
      "created_at": "2024-01-12T09:00:00Z"
    }
  ]
}
```

---

### POST `/api/cases/{uuid}/notes/`
> ADMIN or OFFICER

**Request:**
```json
{ "body": "string (required)" }
```

**Response (201):**
```json
{ "success": true, "message": "Note added", "data": { "note object" } }
```

---

### GET `/api/cases/{uuid}/documents/`
> ADMIN or OFFICER

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "file": "/media/cases/evidence.pdf",
      "original_filename": "evidence.pdf",
      "description": "Exam scan",
      "uploaded_by": 2,
      "uploaded_by_name": "Jane Doe",
      "uploaded_at": "2024-01-12T09:05:00Z"
    }
  ]
}
```

---

### POST `/api/cases/{uuid}/documents/`
> ADMIN or OFFICER

Use `multipart/form-data`.

| Field | Type | Required |
|---|---|---|
| `file` | file | Yes |
| `description` | string | No |

**Response (201):**
```json
{ "success": true, "message": "Document uploaded", "data": { "document object" } }
```

---

## Reports Dashboard
> ADMIN or OFFICER

### GET `/api/reports/dashboard/`

**Response (200):**
```json
{
  "success": true,
  "data": {
    "headline": {
      "total_students": 1200,
      "open_cases": 34,
      "critical_cases": 8,
      "resolved_this_month": 12,
      "new_this_week": 5
    },
    "status_breakdown": [
      { "status": "REPORTED", "count": 10 },
      { "status": "UNDER_REVIEW", "count": 14 },
      { "status": "DECIDED", "count": 6 },
      { "status": "CLOSED", "count": 4 }
    ],
    "monthly_trend": [
      { "month": "Jan", "year": 2024, "count": 8 },
      { "month": "Feb", "year": 2024, "count": 11 }
    ],
    "top_departments": [
      { "name": "Computer Science", "case_count": 15 },
      { "name": "Business", "case_count": 9 }
    ],
    "repeat_offenders_count": 7
  }
}
```

---

## Audit Log
> ADMIN or OFFICER (read-only, append-only)

### GET `/api/audit/`
**Query params:** `page`, `page_size`, `search` (description/resource_id/ip_address), `ordering` (default: `-timestamp`)

**Filter params:**

| Param | Type | Description |
|---|---|---|
| `action` | string | See action choices below |
| `resource_type` | string | e.g. `student`, `case` |
| `resource_id` | string | ID of the affected resource |
| `user` | integer | User ID |

**Action choices:**
`LOGIN` `LOGOUT` `LOGIN_FAILED` `STUDENT_CREATE` `STUDENT_UPDATE` `STUDENT_DEACTIVATE` `BIOMETRIC_ENROLL` `BIOMETRIC_VERIFY_SUCCESS` `BIOMETRIC_VERIFY_FAIL` `CASE_CREATE` `CASE_UPDATE` `CASE_STATUS_CHANGE` `CASE_DOCUMENT_UPLOAD` `USER_CREATE` `USER_DEACTIVATE` `USER_ROLE_CHANGE` `REPORT_EXPORT` `REQUEST_MUTATION`

**Response data array:**
```json
{
  "id": 1,
  "user": 2,
  "user_name": "Jane Doe",
  "action": "CASE_STATUS_CHANGE",
  "resource_type": "case",
  "resource_id": "uuid",
  "description": "Case DIT-2024-0001 moved to DECIDED",
  "before_state": { "status": "UNDER_REVIEW" },
  "after_state": { "status": "DECIDED", "outcome": "WARNING" },
  "ip_address": "192.168.1.10",
  "user_agent": "Mozilla/5.0...",
  "timestamp": "2024-01-12T10:00:00Z"
}
```

---

## Key Implementation Notes

### 1. Token management
Store both `access` and `refresh` in secure storage (not `localStorage` in production). Before any request, check if the access token is close to expiry (8h window) and call `/api/auth/refresh/` proactively.

### 2. ID types
- **Students** and **Cases** → UUIDs in all API paths
- **Users** and **Departments** → integers

### 3. Soft delete
`DELETE` on users and students sets `is_active = false`. List endpoints exclude inactive records by default. Pass `?is_active=false` to show deactivated records.

### 4. Case number vs UUID
Always display `case_number` (e.g. `DIT-2024-0001`) to users. Use the UUID internally for API calls.

### 5. File uploads
Use `Content-Type: multipart/form-data` for:
- `POST /api/students/` (when including `photo`)
- `PATCH /api/students/{uuid}/` (when updating `photo`)
- `POST /api/cases/{uuid}/documents/`

All other endpoints use `application/json`.

### 6. Biometric hash format
The scanner SDK must produce a SHA256 hex string (exactly 64 lowercase or uppercase hex characters). Validate on the client before sending: `/^[a-fA-F0-9]{64}$/`.

### 7. Pagination
Always read `meta.has_next` and `meta.has_previous` to drive pagination controls. Do not assume page count from data array length.

### 8. Filtering vs searching
- `?search=term` — fuzzy/substring across multiple fields
- Filter params (e.g. `?department=1&severity=HIGH`) — exact/range matches; can be combined
