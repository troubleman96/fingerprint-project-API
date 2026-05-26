"""User accounts and role-based access control.

This app owns login identities only. Student data, cases, and biometric records
must stay in their own apps and reference users through foreign keys.
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.TextChoices):
    """System roles used by utils.permissions and the React UI."""

    ADMIN = "ADMIN", "Administrator"
    OFFICER = "OFFICER", "Disciplinary Officer"
    STAFF = "STAFF", "Staff / Clerk"


class CustomUserManager(BaseUserManager):
    """Creates users with email as the login field instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Institutional user account.

    The role field is the main business permission switch. Keep permission logic
    in permission classes and services; avoid scattering role checks through
    templates or serializers.
    """

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    department = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "auth_users"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_officer(self):
        return self.role == Role.OFFICER
