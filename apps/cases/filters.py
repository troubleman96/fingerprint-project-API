import django_filters

from .models import DisciplinaryCase


class CaseFilter(django_filters.FilterSet):
    student = django_filters.UUIDFilter(field_name="student_id")
    incident_type = django_filters.NumberFilter(field_name="incident_type_id")
    date_from = django_filters.DateFilter(field_name="date_of_incident", lookup_expr="gte")
    date_to = django_filters.DateFilter(field_name="date_of_incident", lookup_expr="lte")

    class Meta:
        model = DisciplinaryCase
        fields = ["student", "incident_type", "status", "severity", "date_from", "date_to"]
