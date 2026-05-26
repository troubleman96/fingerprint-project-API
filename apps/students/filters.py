import django_filters

from .models import Student


class StudentFilter(django_filters.FilterSet):
    department = django_filters.NumberFilter(field_name="department_id")
    biometric_enrolled = django_filters.BooleanFilter()
    academic_year = django_filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Student
        fields = ["department", "biometric_enrolled", "academic_year", "is_active"]
