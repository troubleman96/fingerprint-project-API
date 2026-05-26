from rest_framework import serializers


class BiometricEnrollSerializer(serializers.Serializer):
    reg_number = serializers.CharField()
    template_hash = serializers.RegexField(regex=r"^[a-fA-F0-9]{64}$")
    finger_used = serializers.CharField(required=False, default="right_index")
    quality_score = serializers.FloatField(required=False, min_value=0, max_value=1)


class BiometricVerifySerializer(serializers.Serializer):
    template_hash = serializers.RegexField(regex=r"^[a-fA-F0-9]{64}$")
    workstation_id = serializers.CharField(required=False, allow_blank=True)
