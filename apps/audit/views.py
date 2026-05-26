"""Audit API endpoints.

Endpoint:
    GET /api/audit/

Admin and officer users can inspect the audit trail. The model itself prevents
updates/deletes, so this API is intentionally read-only.
"""
from rest_framework.generics import ListAPIView

from utils.permissions import IsAdminOrOfficer

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogListView(ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminOrOfficer]
    queryset = AuditLog.objects.select_related("user").all()
    filterset_fields = ["action", "resource_type", "resource_id", "user"]
    search_fields = ["description", "resource_id", "ip_address"]
    ordering_fields = ["timestamp", "action"]
    ordering = ["-timestamp"]
