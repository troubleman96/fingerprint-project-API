"""Reporting API endpoints.

Endpoint:
    GET /api/reports/dashboard/

The dashboard endpoint intentionally returns multiple chart/stat blocks in one
response so the React dashboard can load without firing many separate requests.
"""
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import DisciplinaryCase
from apps.students.models import Department, Student
from utils.permissions import IsAdminOrOfficer
from utils.response import api_response


class DashboardStatsView(APIView):
    permission_classes = [IsAdminOrOfficer]

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
