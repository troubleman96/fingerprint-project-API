# Cases App

Owns disciplinary case records, evidence documents, internal notes, and workflow transitions.

## Files

- `models.py`: `IncidentType`, `DisciplinaryCase`, `CaseDocument`, `CaseNote`
- `services.py`: workflow transition rules
- `serializers.py`: list/detail/create/action serializers
- `filters.py`: querystring filters
- `views.py`: case ViewSet and custom actions
- `admin.py`: admin registration

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET/POST` | `/api/cases/` | List or create cases |
| `GET/PATCH/DELETE` | `/api/cases/<uuid>/` | Read/update/delete one case |
| `POST` | `/api/cases/<uuid>/transition/` | Move case to next valid status |
| `GET/POST` | `/api/cases/<uuid>/notes/` | List or add internal notes |
| `GET/POST` | `/api/cases/<uuid>/documents/` | List or upload evidence |

## Workflow

Valid transitions:

```text
REPORTED -> UNDER_REVIEW -> DECIDED -> CLOSED
```

Use `transition_case_status()` in `services.py`; do not directly mutate `case.status` in view code.

Decision request:

```json
{
  "status": "DECIDED",
  "outcome": "WARNING",
  "outcome_notes": "Student received formal written warning."
}
```

## Search, Filter, Order

Case list supports:

- `search`: case number, student registration number, student last name, description
- `student`: student UUID
- `incident_type`: incident type ID
- `status`: case status
- `severity`: `LOW`, `MEDIUM`, `HIGH`
- `date_from`, `date_to`: incident date range
- `ordering`: `date_of_incident`, `created_at`, `status`, `severity`

## Important Rules

- Cases use UUID primary keys.
- `case_number` auto-generates as `DIT-YYYY-0001`.
- Student and incident type foreign keys use `PROTECT`.
- Notes are internal and should remain officer/admin visible.
- Evidence uploads preserve `original_filename`.

## Common Changes

- Add a new status: update `Status`, `ALLOWED_TRANSITIONS`, serializers, docs, and frontend labels.
- Add a new outcome: update `Outcome` and any report logic.
- Add notification/email side effects inside `transition_case_status()` so all callers behave the same.
