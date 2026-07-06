from rest_framework import serializers

from .models import SmsLog


class SmsLogSerializer(serializers.ModelSerializer):
    case_number = serializers.CharField(source="case.case_number", read_only=True, default=None)

    class Meta:
        model = SmsLog
        fields = ["id", "recipient", "message", "provider", "status", "error", "case_number", "created_at"]
