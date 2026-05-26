from django.contrib import admin

from .models import Department, Student


admin.site.register(Department)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("reg_number", "first_name", "last_name", "department", "biometric_enrolled", "is_active")
    list_filter = ("department", "biometric_enrolled", "is_active")
    search_fields = ("reg_number", "first_name", "last_name", "email")
