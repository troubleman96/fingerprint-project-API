"""Student API endpoints.

Router-generated endpoints:
    GET    /api/departments/
    POST   /api/departments/
    GET    /api/students/
    POST   /api/students/
    GET    /api/students/<uuid>/
    PUT    /api/students/<uuid>/
    PATCH  /api/students/<uuid>/
    DELETE /api/students/<uuid>/          -> soft-deactivates
    GET    /api/students/<uuid>/cases/    -> cases for one student
"""
from django.db.models import Count, ProtectedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notifications.services import send_sms
from utils.permissions import IsAdmin, IsAdminOrOfficer, IsAdminOrOfficerOrStaff
from utils.response import api_response

from .filters import StudentFilter
from .models import Department, Student
from .serializers import DepartmentSerializer, StudentDetailSerializer, StudentListSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    """CRUD for academic departments."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminOrOfficer]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "code"]


class StudentViewSet(viewsets.ModelViewSet):
    """CRUD for student profiles with search/filter/order support."""

    permission_classes = [IsAdminOrOfficerOrStaff]
    filterset_class = StudentFilter
    search_fields = ["reg_number", "first_name", "last_name", "email"]
    ordering_fields = ["last_name", "reg_number", "created_at"]
    ordering = ["last_name"]

    def get_queryset(self):
        return (
            Student.objects.select_related("department", "registered_by")
            .annotate(case_count=Count("disciplinary_cases"))
            .filter(is_active=True)
        )

    def get_serializer_class(self):
        return StudentListSerializer if self.action == "list" else StudentDetailSerializer

    def perform_create(self, serializer):
        student = serializer.save()
        if student.phone:
            send_sms(
                to=student.phone,
                message=f"DisciplineTrack: {student.full_name} ({student.reg_number}) has been registered in the system.",
            )

    def destroy(self, request, *args, **kwargs):
        student = self.get_object()
        student.is_active = False
        student.save(update_fields=["is_active"])
        return Response(api_response(success=True, message="Student deactivated"), status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], url_path="purge", permission_classes=[IsAdmin])
    def purge(self, request, pk=None):
        """Permanently delete a student record (Admin only) — unlike DELETE, which only deactivates."""
        student = self.get_object()
        try:
            student.delete()
        except ProtectedError:
            return Response(
                api_response(
                    success=False,
                    message="Cannot permanently delete — this student has case history. Deactivate instead.",
                ),
                status=status.HTTP_409_CONFLICT,
            )
        return Response(api_response(success=True, message="Student permanently deleted"), status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="cases")
    def cases(self, request, pk=None):
        """Return all cases for a student without making the frontend build a filter."""
        from apps.cases.models import DisciplinaryCase
        from apps.cases.serializers import CaseListSerializer

        student = self.get_object()
        cases = DisciplinaryCase.objects.filter(student=student).order_by("-date_of_incident")
        return Response(api_response(success=True, data=CaseListSerializer(cases, many=True).data))
