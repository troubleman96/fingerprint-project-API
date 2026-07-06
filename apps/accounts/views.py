"""Accounts API endpoints.

Endpoint summary:
    POST /api/auth/login/                -> returns access/refresh tokens and user data
    POST /api/auth/refresh/              -> handled in config.api_urls by SimpleJWT
    GET  /api/auth/me/                   -> returns the current logged-in user
    POST /api/auth/biometric/enroll/     -> enroll the current user's own fingerprint for login
    POST /api/auth/biometric/login/      -> log in with an enrolled fingerprint instead of a password
    GET  /api/users/                     -> admin lists users
    POST /api/users/                     -> admin creates users
    GET/PUT/PATCH/DELETE /api/users/<id>/ -> admin manages one user
"""
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema

from apps.notifications.services import send_sms
from utils.permissions import IsAdmin
from utils.response import api_response

from .models import CustomUser, Role, StaffBiometricCredential
from .serializers import (
    CustomTokenObtainPairSerializer,
    StaffBiometricEnrollSerializer,
    StaffBiometricLoginSerializer,
    UserReadSerializer,
    UserWriteSerializer,
)


def _admins_with_phone():
    return CustomUser.objects.filter(role=Role.ADMIN, is_active=True).exclude(phone="")


def _alert_login_success(user, request, method="password"):
    """Notify every admin with a phone number whenever anyone logs in."""
    ip = request.META.get("REMOTE_ADDR", "unknown")
    for admin in _admins_with_phone():
        send_sms(
            to=admin.phone,
            message=f"DisciplineTrack: {user.full_name} ({user.email}) logged in via {method} from IP {ip}.",
        )


class LoginView(TokenObtainPairView):
    """Issue JWT token pair. Public endpoint; serializer validates credentials."""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except AuthenticationFailed:
            self._alert_failed_login(request)
            raise
        _alert_login_success(serializer.user, request)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

    def _alert_failed_login(self, request):
        """Security alert — SMS every admin with a phone number on a failed login attempt."""
        email = request.data.get("email", "unknown")
        ip = request.META.get("REMOTE_ADDR", "unknown")
        for admin in _admins_with_phone():
            send_sms(
                to=admin.phone,
                message=f"DisciplineTrack SECURITY ALERT: failed login attempt for '{email}' from IP {ip}.",
            )


class MeView(APIView):
    """Return the authenticated user's current profile."""

    @extend_schema(responses=UserReadSerializer)
    def get(self, request):
        return Response(api_response(success=True, data=UserReadSerializer(request.user).data))


class StaffBiometricEnrollView(APIView):
    """Enroll the current user's own fingerprint as a login credential."""

    @extend_schema(request=StaffBiometricEnrollSerializer, responses=dict)
    def post(self, request):
        serializer = StaffBiometricEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        StaffBiometricCredential.objects.update_or_create(
            user=request.user,
            defaults={
                "template_hash": serializer.validated_data["template_hash"],
                "finger_used": serializer.validated_data.get("finger_used", ""),
            },
        )
        return Response(api_response(success=True, message="Fingerprint login enrolled successfully"))


class StaffBiometricLoginView(APIView):
    """Log in with a previously enrolled fingerprint instead of a password."""

    permission_classes = [AllowAny]

    @extend_schema(request=StaffBiometricLoginSerializer, responses=dict)
    def post(self, request):
        serializer = StaffBiometricLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        credential = StaffBiometricCredential.objects.select_related("user").filter(
            template_hash=serializer.validated_data["template_hash"]
        ).first()
        if not credential or not credential.user.is_active:
            ip = request.META.get("REMOTE_ADDR", "unknown")
            for admin in _admins_with_phone():
                send_sms(
                    to=admin.phone,
                    message=f"DisciplineTrack SECURITY ALERT: failed fingerprint login attempt from IP {ip}.",
                )
            return Response(api_response(success=False, message="Fingerprint not recognised"), status=status.HTTP_401_UNAUTHORIZED)

        user = credential.user
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        _alert_login_success(user, request, method="fingerprint")
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserReadSerializer(user).data,
        })


class UserListCreateView(generics.ListCreateAPIView):
    """Admin-only list/create users."""

    queryset = CustomUser.objects.all().order_by("full_name")
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        return UserWriteSerializer if self.request.method == "POST" else UserReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            api_response(success=True, message="User created successfully", data=UserReadSerializer(user).data),
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only retrieve/update/deactivate one user."""

    queryset = CustomUser.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        return UserWriteSerializer if self.request.method in ("PUT", "PATCH") else UserReadSerializer

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.is_active = False
        user.save(update_fields=["is_active"])
        return Response(api_response(success=True, message="User deactivated"))
