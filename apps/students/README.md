# Students App

Owns academic departments and student profile records.

## Files

- `models.py`: `Department`, `Student`
- `serializers.py`: department, lightweight student list, full student detail
- `filters.py`: querystring filters
- `views.py`: department CRUD, student CRUD, student case lookup
- `admin.py`: admin registration

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET/POST` | `/api/departments/` | List or create departments |
| `GET/PATCH/DELETE` | `/api/departments/<id>/` | Manage one department |
| `GET/POST` | `/api/students/` | List or create students |
| `GET/PATCH/DELETE` | `/api/students/<uuid>/` | Manage one student |
| `GET` | `/api/students/<uuid>/cases/` | List cases for one student |

## Search, Filter, Order

Student list supports:

- `search`: registration number, first name, last name, email
- `department`: department ID
- `biometric_enrolled`: `true` or `false`
- `academic_year`: exact academic year
- `ordering`: `last_name`, `reg_number`, `created_at`

## Important Rules

- Student IDs are UUIDs, not sequential integers.
- `reg_number` is unique and indexed for human lookup.
- `department` uses `PROTECT`, so departments with students cannot be deleted.
- `biometric_enrolled` is only a flag. Fingerprint data belongs to `apps/biometric`.
- Delete is a soft-deactivation through `is_active=False`.

## Common Changes

- Add student fields in `Student`, update serializers/admin, then make migrations.
- Add list filters in `StudentFilter`.
- Add computed list data by annotating in `StudentViewSet.get_queryset()` before reading it in the serializer.
