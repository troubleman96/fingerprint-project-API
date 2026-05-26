"""Case serializers."""
from rest_framework import serializers

from apps.students.serializers import StudentListSerializer

from .models import CaseDocument, CaseNote, DisciplinaryCase, IncidentType


class IncidentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentType
        fields = ["id", "name", "severity_default", "is_active"]


class CaseListSerializer(serializers.ModelSerializer):
    student = StudentListSerializer(read_only=True)
    incident_type_name = serializers.CharField(source="incident_type.name", read_only=True)

    class Meta:
        model = DisciplinaryCase
        fields = [
            "id",
            "case_number",
            "student",
            "incident_type_name",
            "severity",
            "status",
            "outcome",
            "date_of_incident",
            "location",
            "created_at",
        ]


class CaseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplinaryCase
        fields = ["student", "incident_type", "severity", "description", "date_of_incident", "location", "assigned_to"]


class CaseNoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = CaseNote
        fields = ["id", "body", "created_by", "created_by_name", "created_at"]
        read_only_fields = ["id", "created_by", "created_by_name", "created_at"]


class CaseDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.full_name", read_only=True)

    class Meta:
        model = CaseDocument
        fields = ["id", "file", "original_filename", "description", "uploaded_by", "uploaded_by_name", "uploaded_at"]
        read_only_fields = ["id", "original_filename", "uploaded_by", "uploaded_by_name", "uploaded_at"]


class CaseDetailSerializer(serializers.ModelSerializer):
    student = StudentListSerializer(read_only=True)
    incident_type = IncidentTypeSerializer(read_only=True)
    reported_by = serializers.StringRelatedField(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)
    decided_by = serializers.StringRelatedField(read_only=True)
    notes = CaseNoteSerializer(many=True, read_only=True)
    documents = CaseDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = DisciplinaryCase
        fields = "__all__"


class CaseStatusTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=DisciplinaryCase.Status.choices)
    outcome = serializers.ChoiceField(choices=DisciplinaryCase.Outcome.choices, required=False)
    outcome_notes = serializers.CharField(required=False, allow_blank=True)
