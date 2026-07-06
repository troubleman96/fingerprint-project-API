"""Reporting API endpoints.

Endpoints:
    GET /api/reports/dashboard/
    GET /api/reports/export/?dataset=students|cases&format=csv|json

The dashboard endpoint intentionally returns multiple chart/stat blocks in one
response so the React dashboard can load without firing many separate requests.

The export endpoint lets an admin hand this institution's data to another
institution or system (CSV for spreadsheets, JSON for programmatic import).
It is intentionally Admin-only and includes no raw biometric data — only the
fields that already appear elsewhere in the app.
"""
import csv
from datetime import timedelta

from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import DisciplinaryCase
from apps.students.models import Department, Student
from utils.permissions import IsAdmin, IsAdminOrOfficer
from utils.response import api_response


class DashboardStatsView(APIView):
    permission_classes = [IsAdminOrOfficer]

    @extend_schema(responses=dict)
    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        week_ago = now - timedelta(days=7)

        total_students = Student.objects.filter(is_active=True).count()
        open_cases = DisciplinaryCase.objects.filter(
            status__in=[DisciplinaryCase.Status.REPORTED, DisciplinaryCase.Status.UNDER_REVIEW]
        ).count()
        critical_cases = DisciplinaryCase.objects.filter(
            severity=DisciplinaryCase.Severity.HIGH,
            status__in=[DisciplinaryCase.Status.REPORTED, DisciplinaryCase.Status.UNDER_REVIEW],
        ).count()
        resolved_this_month = DisciplinaryCase.objects.filter(
            status=DisciplinaryCase.Status.CLOSED,
            updated_at__gte=month_start,
        ).count()
        new_this_week = DisciplinaryCase.objects.filter(created_at__gte=week_ago).count()

        status_breakdown = DisciplinaryCase.objects.values("status").annotate(count=Count("id")).order_by("status")

        monthly_data = []
        for i in range(6, -1, -1):
            month = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
            month_end = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
            monthly_data.append(
                {
                    "month": month.strftime("%b"),
                    "year": month.year,
                    "count": DisciplinaryCase.objects.filter(
                        date_of_incident__gte=month,
                        date_of_incident__lt=month_end,
                    ).count(),
                }
            )

        top_departments = (
            Department.objects.annotate(case_count=Count("students__disciplinary_cases"))
            .order_by("-case_count")[:5]
            .values("name", "case_count")
        )

        repeat_offenders_count = (
            Student.objects.annotate(case_count=Count("disciplinary_cases")).filter(case_count__gte=2).count()
        )

        return Response(
            api_response(
                success=True,
                data={
                    "headline": {
                        "total_students": total_students,
                        "open_cases": open_cases,
                        "critical_cases": critical_cases,
                        "resolved_this_month": resolved_this_month,
                        "new_this_week": new_this_week,
                    },
                    "status_breakdown": list(status_breakdown),
                    "monthly_trend": monthly_data,
                    "top_departments": list(top_departments),
                    "repeat_offenders_count": repeat_offenders_count,
                },
            )
        )


STUDENT_EXPORT_FIELDS = [
    "reg_number", "first_name", "last_name", "gender", "department",
    "academic_year", "level", "phone", "email", "biometric_enrolled",
    "is_active", "created_at",
]

CASE_EXPORT_FIELDS = [
    "case_number", "student_reg_number", "student_name", "incident_type",
    "severity", "status", "outcome", "description", "date_of_incident",
    "location", "assigned_to", "created_at", "updated_at",
]


def _student_rows():
    for s in Student.objects.select_related("department").order_by("reg_number"):
        yield {
            "reg_number": s.reg_number,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "gender": s.gender,
            "department": s.department.name,
            "academic_year": s.academic_year,
            "level": s.level,
            "phone": s.phone,
            "email": s.email,
            "biometric_enrolled": s.biometric_enrolled,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat(),
        }


def _case_rows():
    qs = DisciplinaryCase.objects.select_related("student", "incident_type", "assigned_to").order_by("-date_of_incident")
    for c in qs:
        yield {
            "case_number": c.case_number,
            "student_reg_number": c.student.reg_number,
            "student_name": c.student.full_name,
            "incident_type": c.incident_type.name,
            "severity": c.severity,
            "status": c.status,
            "outcome": c.outcome,
            "description": c.description,
            "date_of_incident": c.date_of_incident.isoformat(),
            "location": c.location,
            "assigned_to": c.assigned_to.full_name if c.assigned_to else "",
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }


class DataExportView(APIView):
    """Admin-only export of students or cases as CSV or JSON, for use by another institution/system."""

    permission_classes = [IsAdmin]

    DATASETS = {
        "students": (STUDENT_EXPORT_FIELDS, _student_rows),
        "cases": (CASE_EXPORT_FIELDS, _case_rows),
    }

    @extend_schema(responses=dict)
    def get(self, request):
        dataset = request.query_params.get("dataset", "students")
        # NOTE: "filetype", not "format" — DRF reserves ?format= for its own
        # content-negotiation override and 404s before this view even runs
        # if it doesn't recognise the value (e.g. "csv").
        fmt = request.query_params.get("filetype", "csv")

        if dataset not in self.DATASETS:
            return Response(
                api_response(success=False, message=f"Unknown dataset '{dataset}'. Use one of: {list(self.DATASETS)}"),
                status=400,
            )

        fields, row_source = self.DATASETS[dataset]
        rows = list(row_source())
        filename = f"disciplinetrack_{dataset}_{timezone.now().strftime('%Y%m%d')}"

        if fmt == "json":
            response = JsonResponse(rows, safe=False)
            response["Content-Disposition"] = f'attachment; filename="{filename}.json"'
            return response

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}.csv"'
        writer = csv.DictWriter(response, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        return response
