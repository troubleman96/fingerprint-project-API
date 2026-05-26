"""Student serializers.

List endpoints use a lightweight serializer to avoid expensive nested data.
Detail/create/update endpoints use the fuller serializer.
"""
from rest_framework import serializers

from .models import Department, Student


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code"]


class StudentListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    case_count = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "reg_number",
            "first_name",
            "last_name",
            "full_name",
            "department_name",
            "academic_year",
            "biometric_enrolled",
            "is_active",
            "case_count",
        ]


class StudentDetailSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
    )
    registered_by = serializers.StringRelatedField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "reg_number",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "gender",
            "department",
            "department_id",
            "academic_year",
            "level",
            "phone",
            "email",
            "photo",
            "biometric_enrolled",
            "is_active",
            "registered_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "full_name", "biometric_enrolled", "registered_by", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["registered_by"] = self.context["request"].user
        return super().create(validated_data)
