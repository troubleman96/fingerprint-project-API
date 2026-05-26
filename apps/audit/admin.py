from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "resource_type", "resource_id", "ip_address")
    list_filter = ("action", "resource_type", "timestamp")
    search_fields = ("description", "resource_id", "ip_address", "user__email")
    readonly_fields = [field.name for field in AuditLog._meta.fields]
