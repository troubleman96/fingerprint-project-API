# Audit App

Owns the immutable audit trail.

## Files

- `models.py`: append-only `AuditLog`
- `serializers.py`: read serializer
- `utils.py`: `log_action()` helper
- `views.py`: read-only audit list endpoint
- `admin.py`: read-only audit admin presentation

## Endpoint

| Method | Path | Purpose | Permission |
|---|---|---|---|
| `GET` | `/api/audit/` | Search/filter audit log entries | Admin or Officer |

## Querying

Supported filters/search:

- `action`
- `resource_type`
- `resource_id`
- `user`
- `search`: description, resource ID, IP address
- `ordering`: `timestamp`, `action`

## Important Rules

- Audit rows are append-only.
- `save()` raises if you try to update an existing row.
- `delete()` always raises.
- Mutating HTTP requests are logged by `middleware.audit_middleware.RequestAuditMiddleware`.
- Sensitive read actions should call `log_action()` directly.

## Example

```python
from apps.audit.models import AuditLog
from apps.audit.utils import log_action

log_action(
    action=AuditLog.Action.CASE_STATUS_CHANGE,
    description=f"Case {case.case_number} moved to {case.status}",
    user=request.user,
    resource_type="DisciplinaryCase",
    resource_id=str(case.id),
    ip_address=request.META.get("REMOTE_ADDR"),
)
```

## Common Changes

- Add a new audit action in `AuditLog.Action`.
- Add filters in `AuditLogListView` if investigators need more search paths.
- Do not add update/delete APIs for audit records.
