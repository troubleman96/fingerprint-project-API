from django.contrib import admin

from .models import SmsLog


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ("recipient", "status", "provider", "case", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("recipient", "message")
    readonly_fields = [f.name for f in SmsLog._meta.fields]

    def has_add_permission(self, request):
        return False
