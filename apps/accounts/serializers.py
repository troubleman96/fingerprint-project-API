"""Serializers for authentication and user administration."""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import CustomUser


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role/name/email claims to JWTs for frontend role gating."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["full_name"] = user.full_name
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserReadSerializer(self.user).data
        return data


class UserReadSerializer(serializers.ModelSerializer):
    """Safe user fields for API responses."""

    class Meta:
        model = CustomUser
        fields = ["id", "email", "full_name", "role", "department", "phone", "is_active"]
        read_only_fields = fields


class UserWriteSerializer(serializers.ModelSerializer):
    """Admin-only create/update serializer. Password is always hashed."""

    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = CustomUser
        fields = ["email", "full_name", "role", "department", "phone", "password", "is_active"]

    def create(self, validated_data):
        return CustomUser.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
