"""Role-based permissions shared by all apps."""
from rest_framework.permissions import BasePermission

from apps.accounts.models import Role


class IsAdmin(BasePermission):
    """Only ADMIN users may access the view."""

    message = "Access restricted to administrators only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)


class IsAdminOrOfficer(BasePermission):
    """ADMIN and OFFICER users may access the view."""

    message = "Access restricted to officers and administrators."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.OFFICER)
        )


class IsAdminOrOfficerOrStaff(BasePermission):
    """Any authenticated institutional user may access the view."""

    message = "You must be logged in to access this resource."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsOwnerOrAdmin(BasePermission):
    """Allow object edits only by the creator/reporter or an ADMIN user."""

    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True
        owner = getattr(obj, "created_by", None) or getattr(obj, "reported_by", None)
        return owner == request.user
