"""Notifications (SMS) API endpoints.

Endpoints:
    GET /api/notifications/sms-logs/   -> paginated SMS send history (Admin only)
    GET /api/notifications/balance/    -> SMS provider credit balance, if supported
"""
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.permissions import IsAdmin
from utils.response import api_response

from .models import SmsLog
from .serializers import SmsLogSerializer
from .services import check_sms_balance


class SmsLogListView(ListAPIView):
    serializer_class = SmsLogSerializer
    permission_classes = [IsAdmin]
    queryset = SmsLog.objects.select_related("case").all()
    filterset_fields = ["status", "provider"]
    search_fields = ["recipient", "message"]
    ordering_fields = ["created_at", "status"]
    ordering = ["-created_at"]


class SmsBalanceView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response(api_response(success=True, data={"balance": check_sms_balance()}))
