from django.contrib import admin

from .models import CaseDocument, CaseNote, DisciplinaryCase, IncidentType


admin.site.register(IncidentType)
admin.site.register(CaseDocument)
admin.site.register(CaseNote)


@admin.register(DisciplinaryCase)
class DisciplinaryCaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "student", "incident_type", "severity", "status", "date_of_incident")
    list_filter = ("status", "severity", "incident_type")
    search_fields = ("case_number", "student__reg_number", "student__last_name", "description")
