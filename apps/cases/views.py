"""Disciplinary case API endpoints.

Router-generated endpoints:
    GET    /api/incident-types/
    GET    /api/cases/
    POST   /api/cases/
    GET    /api/cases/<uuid>/
    PUT    /api/cases/<uuid>/
    PATCH  /api/cases/<uuid>/
    DELETE /api/cases/<uuid>/

Custom actions:
    POST /api/cases/<uuid>/transition/
    GET  /api/cases/<uuid>/notes/
    POST /api/cases/<uuid>/notes/
    GET  /api/cases/<uuid>/documents/
    POST /api/cases/<uuid>/documents/
"""
from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.notifications.services import send_sms
from utils.permissions import IsAdminOrOfficer, IsAdminOrOfficerOrStaff
from utils.response import api_response

from .filters import CaseFilter
from .models import CaseDocument, CaseNote, DisciplinaryCase, IncidentType
from .serializers import (
    IncidentTypeSerializer,
    CaseCreateSerializer,
    CaseDetailSerializer,
    CaseDocumentSerializer,
    CaseListSerializer,
    CaseNoteSerializer,
    CaseStatusTransitionSerializer,
)
from .services import transition_case_status


class IncidentTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only list of active incident types for UI dropdowns."""

    queryset = IncidentType.objects.filter(is_active=True).order_by("name")
    serializer_class = IncidentTypeSerializer
    permission_classes = [IsAdminOrOfficerOrStaff]
    pagination_class = None


class DisciplinaryCaseViewSet(viewsets.ModelViewSet):
    filterset_class = CaseFilter
    search_fields = ["case_number", "student__reg_number", "student__last_name", "description"]
    ordering_fields = ["date_of_incident", "created_at", "status", "severity"]
    ordering = ["-date_of_incident"]

    def get_queryset(self):
        return DisciplinaryCase.objects.select_related(
            "student",
            "student__department",
            "reported_by",
            "assigned_to",
            "incident_type",
        ).prefetch_related(Prefetch("documents"), Prefetch("notes"))

    def get_serializer_class(self):
        if self.action == "list":
            return CaseListSerializer
        if self.action == "create":
            return CaseCreateSerializer
        return CaseDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAdminOrOfficerOrStaff()]
        return [IsAdminOrOfficer()]

    def perform_create(self, serializer):
        case = serializer.save(reported_by=self.request.user)
        if case.assigned_to and case.assigned_to.phone:
            send_sms(
                to=case.assigned_to.phone,
                message=f"DisciplineTrack: new case {case.case_number} has been assigned to you.",
                case=case,
            )

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        serializer = CaseStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated_case = transition_case_status(
                case=self.get_object(),
                new_status=serializer.validated_data["status"],
                user=request.user,
                outcome=serializer.validated_data.get("outcome"),
                outcome_notes=serializer.validated_data.get("outcome_notes", ""),
            )
        except ValueError as exc:
            return Response(api_response(success=False, message=str(exc)), status=status.HTTP_400_BAD_REQUEST)
        return Response(
            api_response(
                success=True,
                message=f"Case status updated to {updated_case.status}",
                data=CaseDetailSerializer(updated_case).data,
            )
        )

    @action(detail=True, methods=["get", "post"], url_path="notes")
    def notes(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            return Response(api_response(success=True, data=CaseNoteSerializer(case.notes.all(), many=True).data))

        serializer = CaseNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(case=case, created_by=request.user)
        return Response(
            api_response(success=True, message="Note added", data=CaseNoteSerializer(note).data),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get", "post"], url_path="documents")
    def documents(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            return Response(api_response(success=True, data=CaseDocumentSerializer(case.documents.all(), many=True).data))

        serializer = CaseDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc = serializer.save(case=case, uploaded_by=request.user, original_filename=request.data["file"].name)
        return Response(
            api_response(success=True, message="Document uploaded", data=CaseDocumentSerializer(doc).data),
            status=status.HTTP_201_CREATED,
        )
