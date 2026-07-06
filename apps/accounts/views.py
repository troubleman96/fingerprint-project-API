"""Accounts API endpoints.

Endpoint summary:
    POST /api/auth/login/       -> returns access/refresh tokens and user data
    POST /api/auth/refresh/     -> handled in config.api_urls by SimpleJWT
    GET  /api/auth/me/          -> returns the current logged-in user
    GET  /api/users/            -> admin lists users
    POST /api/users/            -> admin creates users
    GET/PUT/PATCH/DELETE /api/users/<id>/ -> admin manages one user
"""
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema

from apps.notifications.services import send_sms
from utils.permissions import IsAdmin
from utils.response import api_response

from .models import CustomUser, Role
from .serializers import CustomTokenObtainPairSerializer, UserReadSerializer, UserWriteSerializer


class LoginView(TokenObtainPairView):
    """Issue JWT token pair. Public endpoint; serializer validates credentials."""

    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            self._alert_failed_login(request)
            raise

    def _alert_failed_login(self, request):
        """Security alert — SMS every admin with a phone number on a failed login attempt."""
        email = request.data.get("email", "unknown")
        ip = request.META.get("REMOTE_ADDR", "unknown")
        admins = CustomUser.objects.filter(role=Role.ADMIN, is_active=True).exclude(phone="")
        for admin in admins:
            send_sms(
                to=admin.phone,
                message=f"DisciplineTrack SECURITY ALERT: failed login attempt for '{email}' from IP {ip}.",
            )


class MeView(APIView):
    """Return the authenticated user's current profile."""

    @extend_schema(responses=UserReadSerializer)
    def get(self, request):
        return Response(api_response(success=True, data=UserReadSerializer(request.user).data))


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
