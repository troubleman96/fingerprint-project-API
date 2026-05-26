# Reports App

Owns computed analytics endpoints. It currently has no database models.

## Files

- `views.py`: dashboard statistics endpoint
- `admin.py`: empty because reports are computed

## Endpoint

| Method | Path | Purpose | Permission |
|---|---|---|---|
| `GET` | `/api/reports/dashboard/` | Dashboard headline stats and chart data | Admin or Officer |

## Response Blocks

The dashboard response returns:

- `headline`: total students, open cases, critical cases, resolved this month, new this week
- `status_breakdown`: count of cases by status
- `monthly_trend`: case counts for the last seven months
- `top_departments`: departments with most linked cases
- `repeat_offenders_count`: students with two or more cases

## Important Rules

- Keep reports read-only unless explicitly implementing exports.
- If a report reveals sensitive data, log it through `apps.audit.utils.log_action()`.
- Prefer aggregate queries (`Count`, `Sum`, filtered querysets) over Python loops on large tables.

## Common Changes

- Add CSV/PDF exports as new endpoints or actions.
- Add date-range filters by reading query params in `DashboardStatsView.get()`.
- If reports get slow, introduce cached snapshots in this app rather than mixing cache state into cases/students.
