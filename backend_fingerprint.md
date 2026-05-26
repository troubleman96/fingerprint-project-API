# Backend Fingerprint — Secure Biometric Disciplinary System
### DRF + PostgreSQL · Role-Based · Audit-First · Multi-Tenant Ready
> Based on: *A Secure Biometric System for Monitoring Student Disciplinary and Crime History in Higher Learning Institutions* — SAWIYA SAYID SALIM, DIT OD23IT

---

## Table of Contents
1. [Project Philosophy](#1-project-philosophy)
2. [Directory Structure](#2-directory-structure)
3. [Django Apps — Separation of Concerns](#3-django-apps--separation-of-concerns)
4. [Settings Architecture](#4-settings-architecture)
5. [App: `accounts` — Auth, Users, RBAC](#5-app-accounts--auth-users-rbac)
6. [App: `students` — Student Profiles & Biometric Linking](#6-app-students--student-profiles--biometric-linking)
7. [App: `biometric` — Fingerprint Verification Layer](#7-app-biometric--fingerprint-verification-layer)
8. [App: `cases` — Disciplinary Case Management](#8-app-cases--disciplinary-case-management)
9. [App: `reports` — Analytics & Exports](#9-app-reports--analytics--exports)
10. [App: `audit` — Immutable Audit Log](#10-app-audit--immutable-audit-log)
11. [Standard API Response Format](#11-standard-api-response-format)
12. [Custom Permissions Matrix](#12-custom-permissions-matrix)
13. [URL Routing](#13-url-routing)
14. [Middleware Stack](#14-middleware-stack)
15. [Environment & Dependencies](#15-environment--dependencies)
16. [Database Schema Summary](#16-database-schema-summary)
17. [Sprint Build Order](#17-sprint-build-order)

---

## 1. Project Philosophy

Every decision in this backend is guided by three principles extracted directly from the project requirements:

- **Security first** — biometric auth, JWT tokens, RBAC, encrypted sensitive fields, audit-everything
- **Clean separation** — each Django app owns one domain; no app reaches into another's models directly
- **Standard responses** — every API response, success or error, follows the same envelope so the React frontend never has to guess

The system serves institutional users (DIT and other higher learning institutions) so the architecture must be **multi-tenant ready** from day one — even if you only deploy for one institution initially.

---

## 2. Directory Structure

```
disciplinetrack/                   # Django project root
│
├── config/                        # Project-level config (not an app)
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                # Shared settings used everywhere
│   │   ├── development.py         # Dev overrides (DEBUG=True, SQLite option)
│   │   └── production.py          # Prod overrides (SSL, S3, strict security)
│   ├── urls.py                    # Root URL dispatcher
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                          # All Django applications live here
│   ├── accounts/                  # Users, auth, JWT, RBAC, roles
│   ├── students/                  # Student profiles, registration, search
│   ├── biometric/                 # Fingerprint enrollment & verification
│   ├── cases/                     # Disciplinary cases, documents, workflow
│   ├── reports/                   # Analytics, aggregations, PDF/CSV export
│   └── audit/                     # Immutable audit log, signals
│
├── utils/                         # Shared helpers (not Django apps)
│   ├── __init__.py
│   ├── response.py                # Standard API response builder
│   ├── permissions.py             # Custom DRF permission classes
│   ├── pagination.py              # Custom paginator
│   ├── filters.py                 # Reusable django-filter base classes
│   ├── exceptions.py              # Custom exception handler
│   └── validators.py              # Shared field validators
│
├── middleware/
│   ├── __init__.py
│   ├── audit_middleware.py        # Auto-logs every request with user+IP
│   └── tenant_middleware.py       # Resolves institution from subdomain/header
│
├── requirements/
│   ├── base.txt                   # Packages for all environments
│   ├── development.txt            # Dev-only (debug toolbar, factory_boy)
│   └── production.txt             # Prod-only (gunicorn, sentry-sdk)
│
├── manage.py
├── .env.example                   # Template — never commit real .env
└── README.md
```

---

## 3. Django Apps — Separation of Concerns

Each app is a self-contained service. The rule: **an app never imports from another app's `models.py`** — cross-app references go through ForeignKey strings or utility functions.

| App | Owns | Does NOT own |
|---|---|---|
| `accounts` | CustomUser, Role, Group | Student data, case data |
| `students` | Student, BiometricLink | Auth logic, case decisions |
| `biometric` | BiometricTemplate, VerificationLog | Student profile fields |
| `cases` | DisciplinaryCase, CaseDocument, CaseNote | Who the user is |
| `reports` | ReportSnapshot, ExportJob | Raw case logic |
| `audit` | AuditLog | Business logic of any kind |

Each app has this internal structure:
```
apps/cases/
├── __init__.py
├── admin.py          # Register models in Django admin
├── apps.py           # AppConfig — wire up signals here
├── filters.py        # django-filter FilterSet for this domain
├── models.py         # Database models
├── permissions.py    # Domain-specific DRF permissions (if any)
├── serializers.py    # DRF serializers (read + write separated)
├── services.py       # Business logic — views call services, not models directly
├── signals.py        # post_save / post_delete signals → audit log
├── urls.py           # URL patterns for this app
├── views.py          # DRF ViewSets — thin, delegate to services
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_serializers.py
    ├── test_views.py
    └── factories.py  # factory_boy factories for test data
```

---

## 4. Settings Architecture

```python
# config/settings/base.py

from pathlib import Path
import environ

# django-environ reads from .env file
env = environ.Env()
environ.Env.read_env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env("DJANGO_SECRET_KEY")

# --------------------------------------------------------------------------
# Application definition — order matters
# --------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",           # DRF — core API framework
    "rest_framework_simplejwt", # JWT auth tokens
    "corsheaders",              # CORS for React frontend
    "django_filters",           # Querystring filtering
    "drf_spectacular",          # OpenAPI schema (Swagger UI)
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.students",
    "apps.biometric",
    "apps.cases",
    "apps.reports",
    "apps.audit",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# --------------------------------------------------------------------------
# Custom user model — MUST be set before any migration
# --------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomUser"

# --------------------------------------------------------------------------
# DRF global configuration
# --------------------------------------------------------------------------
REST_FRAMEWORK = {
    # All endpoints require a valid JWT unless explicitly overridden
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Use our custom response envelope on all errors
    "EXCEPTION_HANDLER": "utils.exceptions.custom_exception_handler",
    # Consistent pagination across all list endpoints
    "DEFAULT_PAGINATION_CLASS": "utils.pagination.StandardResultsPagination",
    "PAGE_SIZE": 25,
    # Filtering, searching, ordering on all ViewSets
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    # OpenAPI schema renderer
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# --------------------------------------------------------------------------
# JWT settings (SimpleJWT)
# --------------------------------------------------------------------------
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=8),   # One working day
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Embed role in token so frontend can gate UI without extra API call
    "TOKEN_OBTAIN_SERIALIZER": "apps.accounts.serializers.CustomTokenObtainPairSerializer",
}

# --------------------------------------------------------------------------
# Database — PostgreSQL in all environments
# --------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL")
    # Example: DATABASE_URL=postgres://user:pass@localhost:5432/disciplinetrack
}

# --------------------------------------------------------------------------
# CORS — allow the React dev server and production domain
# --------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_CREDENTIALS = True
```

---

## 5. App: `accounts` — Auth, Users, RBAC

### Models

```python
# apps/accounts/models.py

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class Role(models.TextChoices):
    """
    Three roles defined in the project spec (Chapter 3 - RBAC Engine).
    Using TextChoices so the value stored in DB is a readable string,
    not an integer — easier to audit and debug.
    """
    ADMIN = "ADMIN", "Administrator"
    OFFICER = "OFFICER", "Disciplinary Officer"
    STAFF = "STAFF", "Staff / Clerk"


class CustomUserManager(BaseUserManager):
    """
    Custom manager required because we use email as the login field,
    not username (username is kept only for display).
    """

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
    """
    Institutional user account.

    Every person who can log into DisciplineTrack — admin, officer, or
    staff clerk — is a CustomUser. The `role` field drives all permission
    checks via our custom DRF permission classes.

    Biometric authentication is handled separately in the `biometric` app;
    this model only handles credential-based auth and JWT issuance.
    """

    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    department = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)   # Django admin access
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # Institution FK — for future multi-tenant support
    # institution = models.ForeignKey("institutions.Institution", ...)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "auth_users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.role})"

    @property
    def is_admin(self):
        return self.role == Role.ADMIN

    @property
    def is_officer(self):
        return self.role == Role.OFFICER
```

### Serializers

```python
# apps/accounts/serializers.py

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import CustomUser, Role


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT serializer to embed the user's role and
    display name in the token payload.

    The React frontend reads this from the decoded token to:
    - Show/hide menu items based on role
    - Display the logged-in user's name in the sidebar
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Embed extra claims — readable in React without an extra API call
        token["role"] = user.role
        token["full_name"] = user.full_name
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add user details to the login response body as well
        data["user"] = {
            "id": self.user.id,
            "email": self.user.email,
            "full_name": self.user.full_name,
            "role": self.user.role,
        }
        return data


class UserReadSerializer(serializers.ModelSerializer):
    """Read-only serializer — used for listing users and returning
    user details in nested case serializers."""

    class Meta:
        model = CustomUser
        fields = ["id", "email", "full_name", "role", "department", "is_active"]
        read_only_fields = fields


class UserWriteSerializer(serializers.ModelSerializer):
    """Write serializer — used by Admin only to create/update users.
    Password is write-only and hashed on save."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ["email", "full_name", "role", "department", "phone", "password"]

    def create(self, validated_data):
        # Use manager so password is properly hashed
        return CustomUser.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
```

### Views

```python
# apps/accounts/views.py

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from utils.response import api_response
from utils.permissions import IsAdmin
from .models import CustomUser
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserReadSerializer,
    UserWriteSerializer,
)


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login/

    Issues JWT access + refresh tokens.
    Response includes the token pair AND decoded user details
    (role, name, email) so the frontend doesn't need a second call.

    Uses CustomTokenObtainPairSerializer which embeds role in the JWT.
    """
    serializer_class = CustomTokenObtainPairSerializer


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/users/     — List all users (Admin only)
    POST /api/users/     — Create a new user account (Admin only)
    """
    queryset = CustomUser.objects.all().order_by("full_name")
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        # Use write serializer for POST, read serializer for GET
        if self.request.method == "POST":
            return UserWriteSerializer
        return UserReadSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            api_response(
                success=True,
                message="User created successfully",
                data=UserReadSerializer(user).data,
            ),
            status=status.HTTP_201_CREATED,
        )


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/users/<id>/   — Get user detail
    PUT    /api/users/<id>/   — Update user (Admin only)
    DELETE /api/users/<id>/   — Deactivate user (Admin only, soft-delete)
    """
    queryset = CustomUser.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserWriteSerializer
        return UserReadSerializer

    def destroy(self, request, *args, **kwargs):
        # Soft-delete: set is_active=False instead of deleting the record.
        # Preserves audit trail integrity — you can't delete a user who
        # appears in audit log entries.
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response(
            api_response(success=True, message="User deactivated"),
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """
    GET /api/auth/me/

    Returns the currently authenticated user's profile.
    Used by the React frontend on app load to verify token validity
    and get fresh user data.
    """

    def get(self, request):
        serializer = UserReadSerializer(request.user)
        return Response(api_response(success=True, data=serializer.data))
```

---

## 6. App: `students` — Student Profiles & Biometric Linking

### Models

```python
# apps/students/models.py

from django.db import models
import uuid


class Department(models.Model):
    """
    Academic department (e.g. Computer Studies, Business Administration).
    Normalised into its own table so reports can group by department.
    """
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = "departments"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    """
    Core student profile.

    The `reg_number` is the institution's registration number (e.g. 220229358370).
    It is used as the primary human identifier in disciplinary cases.

    `biometric_enrolled` is a simple flag; the actual template reference lives
    in the `biometric` app to keep that concern isolated.

    Photo is stored as a file upload; in production this goes to S3/object storage
    via django-storages — the field path is relative to MEDIA_ROOT.
    """

    # Use UUID as PK so IDs are not sequential/guessable in API responses
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    reg_number = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
        blank=True,
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,   # Can't delete a department with students
        related_name="students",
    )
    academic_year = models.CharField(max_length=20)  # e.g. "2023/2024"
    level = models.CharField(max_length=50, blank=True)  # e.g. "NTA Level 6"
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to="students/photos/%Y/", null=True, blank=True)
    biometric_enrolled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)  # False = graduated / expelled
    registered_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="registered_students",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "students"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["reg_number"]),
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.reg_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def case_count(self):
        """Quick access to total disciplinary cases — used in serializer."""
        return self.disciplinary_cases.count()
```

### Serializers

```python
# apps/students/serializers.py

from rest_framework import serializers
from .models import Student, Department


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "code"]


class StudentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for list endpoints.
    Does not include nested case data — avoids N+1 query issues on lists.
    """
    department_name = serializers.CharField(source="department.name", read_only=True)
    case_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "reg_number", "first_name", "last_name", "full_name",
            "department_name", "academic_year", "biometric_enrolled",
            "is_active", "case_count",
        ]
        read_only_fields = ["id", "full_name", "case_count"]


class StudentDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for detail/create/update endpoints.
    Includes department object and registered_by user info.
    """
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source="department",
        write_only=True,
    )
    registered_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Student
        fields = [
            "id", "reg_number", "first_name", "last_name", "full_name",
            "date_of_birth", "gender", "department", "department_id",
            "academic_year", "level", "phone", "email", "photo",
            "biometric_enrolled", "is_active", "registered_by",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "full_name", "biometric_enrolled", "registered_by", "created_at", "updated_at"]

    def create(self, validated_data):
        # Automatically set registered_by to the requesting user
        validated_data["registered_by"] = self.context["request"].user
        return super().create(validated_data)
```

### Views

```python
# apps/students/views.py

from rest_framework import generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django.db.models import Count

from utils.response import api_response
from utils.permissions import IsAdminOrOfficer
from .models import Student, Department
from .serializers import StudentListSerializer, StudentDetailSerializer, DepartmentSerializer
from .filters import StudentFilter


class StudentViewSet(ModelViewSet):
    """
    ViewSet handles all CRUD for students.

    Endpoints auto-generated by DRF router:
      GET    /api/students/              — list (with search, filter, order)
      POST   /api/students/              — create new student
      GET    /api/students/<id>/         — retrieve detail
      PUT    /api/students/<id>/         — full update
      PATCH  /api/students/<id>/         — partial update
      DELETE /api/students/<id>/         — deactivate (soft delete)

    Custom action:
      GET    /api/students/<id>/cases/   — cases for this student
    """

    permission_classes = [IsAdminOrOfficer]
    filterset_class = StudentFilter
    search_fields = ["reg_number", "first_name", "last_name", "email"]
    ordering_fields = ["last_name", "reg_number", "created_at"]
    ordering = ["last_name"]

    def get_queryset(self):
        # Annotate case_count on the queryset so the serializer can read it
        # without triggering extra queries per row (N+1 prevention)
        return (
            Student.objects.select_related("department", "registered_by")
            .annotate(case_count=Count("disciplinary_cases"))
            .filter(is_active=True)
        )

    def get_serializer_class(self):
        # List uses the lightweight serializer; everything else uses full
        if self.action == "list":
            return StudentListSerializer
        return StudentDetailSerializer

    def destroy(self, request, *args, **kwargs):
        """
        Override DELETE to do a soft delete.
        Students are never hard-deleted — disciplinary records reference them.
        """
        student = self.get_object()
        student.is_active = False
        student.save()
        return Response(
            api_response(success=True, message="Student deactivated"),
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="cases")
    def cases(self, request, pk=None):
        """
        GET /api/students/<id>/cases/

        Returns all disciplinary cases for this student.
        Imported here to avoid circular imports — cases app knows about students,
        but students app should NOT know about cases.
        """
        from apps.cases.models import DisciplinaryCase
        from apps.cases.serializers import CaseListSerializer

        student = self.get_object()
        cases = DisciplinaryCase.objects.filter(student=student).order_by("-date_of_incident")
        serializer = CaseListSerializer(cases, many=True)
        return Response(api_response(success=True, data=serializer.data))
```

---

## 7. App: `biometric` — Fingerprint Verification Layer

```python
# apps/biometric/models.py

from django.db import models
import uuid


class BiometricTemplate(models.Model):
    """
    Stores the fingerprint template reference for a student.

    SECURITY RULE: We NEVER store raw fingerprint image data.
    The scanner SDK processes the image and produces a binary template.
    We store a SHA-256 hash of that template — enough to verify
    but impossible to reconstruct into an actual fingerprint.

    The `template_hash` is compared against a fresh scan at login time.
    The actual matching is done by the scanner SDK running locally
    (on the workstation where the USB scanner is connected).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="biometric_template",
    )
    # Hash of the SDK-produced template — never the raw image
    template_hash = models.CharField(max_length=64, unique=True)
    # Finger used: right_thumb, right_index, left_thumb, left_index
    finger_used = models.CharField(max_length=20, default="right_index")
    quality_score = models.FloatField(null=True, blank=True)  # 0.0 - 1.0
    enrolled_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="enrolled_biometrics",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "biometric_templates"

    def __str__(self):
        return f"Template for {self.student.reg_number}"


class BiometricVerificationLog(models.Model):
    """
    Every fingerprint verification attempt is logged here — success or failure.

    This table is the security backbone:
    - Detect brute-force attempts (many failures in short time)
    - Prove a user was authenticated at a specific time
    - Feed into the main audit log
    """

    class Result(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        ERROR = "ERROR", "Error"  # Scanner hardware error

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="verification_attempts",
    )
    result = models.CharField(max_length=10, choices=Result.choices)
    match_score = models.FloatField(null=True, blank=True)  # SDK confidence score
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    workstation_id = models.CharField(max_length=100, blank=True)  # Identifies the scanner terminal
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "biometric_verification_logs"
        indexes = [
            models.Index(fields=["student", "attempted_at"]),
            models.Index(fields=["result"]),
        ]
```

```python
# apps/biometric/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from utils.response import api_response
from utils.permissions import IsAdminOrOfficer
from apps.students.models import Student
from .models import BiometricTemplate, BiometricVerificationLog
from .serializers import BiometricEnrollSerializer, BiometricVerifySerializer


class BiometricEnrollView(APIView):
    """
    POST /api/biometric/enroll/

    Registers a fingerprint template hash for a student.

    The fingerprint scanner on the client workstation produces the template.
    The local agent (or JS in the browser) sends the template_hash to this
    endpoint. We store the hash, mark the student as enrolled.

    Only Admin or Officer can enroll students.
    """

    permission_classes = [IsAdminOrOfficer]

    def post(self, request):
        serializer = BiometricEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reg_number = serializer.validated_data["reg_number"]
        template_hash = serializer.validated_data["template_hash"]
        finger_used = serializer.validated_data.get("finger_used", "right_index")

        try:
            student = Student.objects.get(reg_number=reg_number)
        except Student.DoesNotExist:
            return Response(
                api_response(success=False, message="Student not found"),
                status=status.HTTP_404_NOT_FOUND,
            )

        # Upsert: create or update the template for this student
        template, created = BiometricTemplate.objects.update_or_create(
            student=student,
            defaults={
                "template_hash": template_hash,
                "finger_used": finger_used,
                "enrolled_by": request.user,
                "enrolled_at": timezone.now(),
            },
        )

        # Mark student as enrolled
        student.biometric_enrolled = True
        student.save(update_fields=["biometric_enrolled"])

        action = "enrolled" if created else "re-enrolled"
        return Response(
            api_response(success=True, message=f"Student biometric {action} successfully"),
            status=status.HTTP_200_OK,
        )


class BiometricVerifyView(APIView):
    """
    POST /api/biometric/verify/

    Verifies a fingerprint hash against the stored template.

    The scanner agent sends the hash of the live scan. We compare it
    against the stored template_hash. On match, return the student details.

    This endpoint is used when:
    - A staff member wants to look up who just scanned their finger
    - Pre-filling a new case form by having the student scan in
    """

    def post(self, request):
        serializer = BiometricVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        incoming_hash = serializer.validated_data["template_hash"]
        ip = request.META.get("REMOTE_ADDR")

        try:
            template = BiometricTemplate.objects.select_related("student").get(
                template_hash=incoming_hash
            )
            student = template.student

            # Log the successful verification
            BiometricVerificationLog.objects.create(
                student=student,
                result=BiometricVerificationLog.Result.SUCCESS,
                ip_address=ip,
            )

            # Update last verified timestamp
            template.last_verified_at = timezone.now()
            template.save(update_fields=["last_verified_at"])

            return Response(
                api_response(
                    success=True,
                    message="Biometric verified",
                    data={
                        "student_id": str(student.id),
                        "reg_number": student.reg_number,
                        "full_name": student.full_name,
                        "department": student.department.name,
                    },
                )
            )

        except BiometricTemplate.DoesNotExist:
            # Log the failed attempt for security monitoring
            BiometricVerificationLog.objects.create(
                result=BiometricVerificationLog.Result.FAILURE,
                ip_address=ip,
                student_id=None,  # Unknown student
            )
            return Response(
                api_response(success=False, message="Fingerprint not recognised"),
                status=status.HTTP_401_UNAUTHORIZED,
            )
```

---

## 8. App: `cases` — Disciplinary Case Management

### Models

```python
# apps/cases/models.py

from django.db import models
import uuid


class IncidentType(models.Model):
    """
    Lookup table for incident types (e.g. Academic Fraud, Physical Misconduct).
    Stored in DB so Admin can configure without code changes.
    """
    name = models.CharField(max_length=100, unique=True)
    severity_default = models.CharField(
        max_length=10,
        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")],
        default="MEDIUM",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "incident_types"

    def __str__(self):
        return self.name


class DisciplinaryCase(models.Model):
    """
    Core entity of the entire system.

    Represents one disciplinary incident involving one student.
    A student can have many cases; each case is tracked independently
    through its lifecycle from REPORTED → UNDER_REVIEW → DECIDED → CLOSED.

    The `outcome` field is only populated once the case reaches DECIDED.
    Before that, it should be null/blank.
    """

    class Status(models.TextChoices):
        REPORTED = "REPORTED", "Reported"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        DECIDED = "DECIDED", "Decided"
        CLOSED = "CLOSED", "Closed"

    class Severity(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"

    class Outcome(models.TextChoices):
        CLEARED = "CLEARED", "Cleared"
        WARNING = "WARNING", "Formal Warning"
        SUSPENSION = "SUSPENSION", "Suspension"
        EXPULSION = "EXPULSION", "Expulsion"
        REFERRED = "REFERRED", "Referred to Police"  # Crime cases

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Human-readable case number — e.g. "DIT-2024-0441"
    case_number = models.CharField(max_length=50, unique=True, db_index=True)

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.PROTECT,   # Never delete a student with open cases
        related_name="disciplinary_cases",
    )
    incident_type = models.ForeignKey(
        IncidentType,
        on_delete=models.PROTECT,
        related_name="cases",
    )
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REPORTED)
    outcome = models.CharField(max_length=20, choices=Outcome.choices, blank=True)

    description = models.TextField()
    date_of_incident = models.DateField()
    location = models.CharField(max_length=255, blank=True)

    # Who filed the case (Staff / Clerk)
    reported_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="reported_cases",
    )
    # Who is handling the review (Officer)
    assigned_to = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
    )
    # Decision details
    outcome_notes = models.TextField(blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    decided_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="decided_cases",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "disciplinary_cases"
        ordering = ["-date_of_incident"]
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["status"]),
            models.Index(fields=["date_of_incident"]),
            models.Index(fields=["case_number"]),
        ]

    def __str__(self):
        return f"{self.case_number} — {self.student.reg_number}"

    def save(self, *args, **kwargs):
        # Auto-generate case number on first save if not set
        if not self.case_number:
            self.case_number = self._generate_case_number()
        super().save(*args, **kwargs)

    def _generate_case_number(self):
        from django.utils import timezone
        year = timezone.now().year
        # Count existing cases this year and zero-pad
        count = DisciplinaryCase.objects.filter(
            created_at__year=year
        ).count() + 1
        return f"DIT-{year}-{count:04d}"


class CaseDocument(models.Model):
    """
    Evidence files attached to a disciplinary case.
    Supports images, PDFs, scanned forms — anything submitted as evidence.
    """

    case = models.ForeignKey(
        DisciplinaryCase,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="cases/documents/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_documents"

    def __str__(self):
        return f"{self.original_filename} → {self.case.case_number}"


class CaseNote(models.Model):
    """
    Internal notes on a case — visible only to Officers and Admin.
    Forms the paper trail of the review process.
    """

    case = models.ForeignKey(
        DisciplinaryCase,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    body = models.TextField()
    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_notes"
        ordering = ["-created_at"]
```

### Services

```python
# apps/cases/services.py

from django.utils import timezone
from django.db import transaction

from .models import DisciplinaryCase


# Define valid state transitions — only these are allowed
ALLOWED_TRANSITIONS = {
    DisciplinaryCase.Status.REPORTED: [DisciplinaryCase.Status.UNDER_REVIEW],
    DisciplinaryCase.Status.UNDER_REVIEW: [DisciplinaryCase.Status.DECIDED],
    DisciplinaryCase.Status.DECIDED: [DisciplinaryCase.Status.CLOSED],
    DisciplinaryCase.Status.CLOSED: [],  # Terminal state
}


def transition_case_status(case: DisciplinaryCase, new_status: str, user, outcome: str = None, outcome_notes: str = "") -> DisciplinaryCase:
    """
    Validates and applies a status transition on a case.

    This is a service function — the view calls this instead of directly
    mutating the model. Centralising logic here makes it:
    - Testable without an HTTP request
    - Easy to add side effects (email, notification) in one place
    - The single source of truth for what status changes are valid

    Raises ValueError if the transition is not allowed.
    """

    allowed_next = ALLOWED_TRANSITIONS.get(case.status, [])
    if new_status not in allowed_next:
        raise ValueError(
            f"Cannot transition from '{case.status}' to '{new_status}'. "
            f"Allowed next statuses: {allowed_next}"
        )

    with transaction.atomic():
        case.status = new_status

        # If moving to DECIDED, record who decided and when
        if new_status == DisciplinaryCase.Status.DECIDED:
            if not outcome:
                raise ValueError("Outcome is required when deciding a case")
            case.outcome = outcome
            case.outcome_notes = outcome_notes
            case.decided_by = user
            case.decided_at = timezone.now()

        case.save()

    return case
```

### Views

```python
# apps/cases/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

from utils.response import api_response
from utils.permissions import IsAdminOrOfficer, IsAdminOrOfficerOrStaff
from .models import DisciplinaryCase, CaseDocument, CaseNote
from .serializers import (
    CaseListSerializer,
    CaseDetailSerializer,
    CaseCreateSerializer,
    CaseStatusTransitionSerializer,
    CaseNoteSerializer,
    CaseDocumentSerializer,
)
from .services import transition_case_status
from .filters import CaseFilter


class DisciplinaryCaseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for disciplinary cases.

    GET    /api/cases/                     — List (filter by status, type, student, date range)
    POST   /api/cases/                     — Create new case
    GET    /api/cases/<id>/                — Full case detail
    PUT    /api/cases/<id>/                — Update case
    PATCH  /api/cases/<id>/                — Partial update

    Custom actions:
    POST   /api/cases/<id>/transition/     — Advance case status
    POST   /api/cases/<id>/notes/          — Add internal note
    GET    /api/cases/<id>/notes/          — List notes on case
    POST   /api/cases/<id>/documents/      — Upload evidence document
    GET    /api/cases/<id>/documents/      — List documents
    """

    filterset_class = CaseFilter
    search_fields = ["case_number", "student__reg_number", "student__last_name", "description"]
    ordering_fields = ["date_of_incident", "created_at", "status", "severity"]
    ordering = ["-date_of_incident"]

    def get_queryset(self):
        return (
            DisciplinaryCase.objects
            .select_related("student", "student__department", "reported_by", "assigned_to", "incident_type")
            .prefetch_related(
                Prefetch("documents"),
                Prefetch("notes"),
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CaseListSerializer
        if self.action == "create":
            return CaseCreateSerializer
        return CaseDetailSerializer

    def get_permissions(self):
        """
        Staff can create cases (file reports).
        Officers and Admin can do everything else.
        """
        if self.action == "create":
            return [IsAdminOrOfficerOrStaff()]
        return [IsAdminOrOfficer()]

    def perform_create(self, serializer):
        # Automatically assign reported_by to the current user
        serializer.save(reported_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="transition")
    def transition(self, request, pk=None):
        """
        POST /api/cases/<id>/transition/

        Body: { "status": "UNDER_REVIEW" }
              { "status": "DECIDED", "outcome": "WARNING", "outcome_notes": "..." }
        """
        case = self.get_object()
        serializer = CaseStatusTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_case = transition_case_status(
                case=case,
                new_status=serializer.validated_data["status"],
                user=request.user,
                outcome=serializer.validated_data.get("outcome"),
                outcome_notes=serializer.validated_data.get("outcome_notes", ""),
            )
        except ValueError as e:
            return Response(
                api_response(success=False, message=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            api_response(
                success=True,
                message=f"Case status updated to {updated_case.status}",
                data=CaseDetailSerializer(updated_case).data,
            )
        )

    @action(detail=True, methods=["get", "post"], url_path="notes")
    def notes(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            notes = case.notes.select_related("created_by").all()
            return Response(api_response(success=True, data=CaseNoteSerializer(notes, many=True).data))

        # POST — add a new note
        serializer = CaseNoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = serializer.save(case=case, created_by=request.user)
        return Response(
            api_response(success=True, message="Note added", data=CaseNoteSerializer(note).data),
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get", "post"], url_path="documents")
    def documents(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            docs = case.documents.select_related("uploaded_by").all()
            return Response(api_response(success=True, data=CaseDocumentSerializer(docs, many=True).data))

        # POST — upload a document
        serializer = CaseDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        doc = serializer.save(
            case=case,
            uploaded_by=request.user,
            original_filename=request.data["file"].name,
        )
        return Response(
            api_response(success=True, message="Document uploaded", data=CaseDocumentSerializer(doc).data),
            status=status.HTTP_201_CREATED,
        )
```

---

## 9. App: `reports` — Analytics & Exports

```python
# apps/reports/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from utils.response import api_response
from utils.permissions import IsAdminOrOfficer
from apps.cases.models import DisciplinaryCase
from apps.students.models import Student, Department


class DashboardStatsView(APIView):
    """
    GET /api/reports/dashboard/

    Returns all statistics needed for the React dashboard in a single call:
    - Total students, open/critical cases, resolved this month
    - Cases grouped by status
    - Cases per month for the last 7 months (bar chart data)
    - Top departments by case count
    - Repeat offenders (students with 2+ cases)

    Using a single endpoint avoids multiple round-trips from the React
    dashboard on initial load.
    """

    permission_classes = [IsAdminOrOfficer]

    def get(self, request):
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0)
        week_ago = now - timedelta(days=7)

        # --- Headline stats ---
        total_students = Student.objects.filter(is_active=True).count()
        open_cases = DisciplinaryCase.objects.filter(
            status__in=[DisciplinaryCase.Status.REPORTED, DisciplinaryCase.Status.UNDER_REVIEW]
        ).count()
        critical_cases = DisciplinaryCase.objects.filter(
            severity=DisciplinaryCase.Severity.HIGH,
            status__in=[DisciplinaryCase.Status.REPORTED, DisciplinaryCase.Status.UNDER_REVIEW]
        ).count()
        resolved_this_month = DisciplinaryCase.objects.filter(
            status=DisciplinaryCase.Status.CLOSED,
            updated_at__gte=month_start,
        ).count()
        new_this_week = DisciplinaryCase.objects.filter(created_at__gte=week_ago).count()

        # --- Status breakdown ---
        status_breakdown = (
            DisciplinaryCase.objects
            .values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )

        # --- Monthly trend (last 7 months) ---
        monthly_data = []
        for i in range(6, -1, -1):
            # Go back i months from current month
            month = (now.replace(day=1) - timedelta(days=i * 28)).replace(day=1)
            month_end = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
            count = DisciplinaryCase.objects.filter(
                date_of_incident__gte=month,
                date_of_incident__lt=month_end,
            ).count()
            monthly_data.append({
                "month": month.strftime("%b"),
                "year": month.year,
                "count": count,
            })

        # --- Top departments by case count ---
        top_departments = (
            Department.objects
            .annotate(case_count=Count("students__disciplinary_cases"))
            .order_by("-case_count")[:5]
            .values("name", "case_count")
        )

        # --- Repeat offenders (2+ cases) ---
        repeat_offenders_count = (
            Student.objects
            .annotate(case_count=Count("disciplinary_cases"))
            .filter(case_count__gte=2)
            .count()
        )

        return Response(api_response(
            success=True,
            data={
                "headline": {
                    "total_students": total_students,
                    "open_cases": open_cases,
                    "critical_cases": critical_cases,
                    "resolved_this_month": resolved_this_month,
                    "new_this_week": new_this_week,
                },
                "status_breakdown": list(status_breakdown),
                "monthly_trend": monthly_data,
                "top_departments": list(top_departments),
                "repeat_offenders_count": repeat_offenders_count,
            }
        ))
```

---

## 10. App: `audit` — Immutable Audit Log

```python
# apps/audit/models.py

from django.db import models
from django.conf import settings


class AuditLog(models.Model):
    """
    Immutable record of every meaningful action in the system.

    CRITICAL RULES:
    1. This model has no `update` or `delete` methods — records are append-only.
    2. Every write to students, cases, biometric data triggers an entry here.
    3. This table is NEVER cleaned up by the application — only by a DBA
       with explicit written authorisation.

    Populated automatically via:
    - Django signals in each app's signals.py
    - Middleware for request-level logging
    - Explicit calls in sensitive views (login, role change, deletion)
    """

    class Action(models.TextChoices):
        # Auth events
        LOGIN = "LOGIN", "User Login"
        LOGOUT = "LOGOUT", "User Logout"
        LOGIN_FAILED = "LOGIN_FAILED", "Failed Login Attempt"
        # Student events
        STUDENT_CREATE = "STUDENT_CREATE", "Student Created"
        STUDENT_UPDATE = "STUDENT_UPDATE", "Student Updated"
        STUDENT_DEACTIVATE = "STUDENT_DEACTIVATE", "Student Deactivated"
        # Biometric events
        BIOMETRIC_ENROLL = "BIOMETRIC_ENROLL", "Biometric Enrolled"
        BIOMETRIC_VERIFY_SUCCESS = "BIOMETRIC_VERIFY_SUCCESS", "Biometric Verified"
        BIOMETRIC_VERIFY_FAIL = "BIOMETRIC_VERIFY_FAIL", "Biometric Failed"
        # Case events
        CASE_CREATE = "CASE_CREATE", "Case Created"
        CASE_UPDATE = "CASE_UPDATE", "Case Updated"
        CASE_STATUS_CHANGE = "CASE_STATUS_CHANGE", "Case Status Changed"
        CASE_DOCUMENT_UPLOAD = "CASE_DOCUMENT_UPLOAD", "Document Uploaded"
        # User admin events
        USER_CREATE = "USER_CREATE", "User Account Created"
        USER_DEACTIVATE = "USER_DEACTIVATE", "User Account Deactivated"
        USER_ROLE_CHANGE = "USER_ROLE_CHANGE", "User Role Changed"
        # Report events
        REPORT_EXPORT = "REPORT_EXPORT", "Report Exported"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,      # Null for system-generated events
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    # Which model type and ID was affected
    resource_type = models.CharField(max_length=100, blank=True)  # e.g. "DisciplinaryCase"
    resource_id = models.CharField(max_length=100, blank=True)    # e.g. the UUID
    # Human-readable summary of what happened
    description = models.TextField()
    # JSON snapshot of changed data (before/after for updates)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        # Composite index for the most common query: who did what, when
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        user_str = self.user.full_name if self.user else "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_str} — {self.action}"

    # Prevent updates and deletes at the model level
    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog entries cannot be deleted.")
```

```python
# apps/audit/utils.py

from .models import AuditLog


def log_action(action: str, description: str, user=None, resource_type: str = "",
               resource_id: str = "", before_state=None, after_state=None,
               ip_address: str = None, user_agent: str = "") -> AuditLog:
    """
    Convenience function to write an audit log entry.

    Call this from any view, service, or signal that needs to record an action.

    Usage:
        from apps.audit.utils import log_action

        log_action(
            action=AuditLog.Action.CASE_STATUS_CHANGE,
            description=f"Case {case.case_number} moved to {new_status}",
            user=request.user,
            resource_type="DisciplinaryCase",
            resource_id=str(case.id),
            ip_address=request.META.get("REMOTE_ADDR"),
        )
    """
    return AuditLog.objects.create(
        action=action,
        description=description,
        user=user,
        resource_type=resource_type,
        resource_id=resource_id,
        before_state=before_state,
        after_state=after_state,
        ip_address=ip_address,
        user_agent=user_agent,
    )
```

---

## 11. Standard API Response Format

Every single response — success, validation error, 404, 500 — uses this envelope. The React frontend only needs to check `success` and `message`.

```python
# utils/response.py

from typing import Any, Optional


def api_response(
    success: bool,
    message: str = "",
    data: Any = None,
    errors: Any = None,
    meta: Optional[dict] = None,
) -> dict:
    """
    Standard API response envelope used by every endpoint.

    Success response shape:
    {
        "success": true,
        "message": "Case created successfully",
        "data": { ... },
        "errors": null,
        "meta": { "page": 1, "total": 38 }   # Optional, for lists
    }

    Error response shape:
    {
        "success": false,
        "message": "Validation failed",
        "data": null,
        "errors": { "reg_number": ["This field is required."] },
        "meta": null
    }
    """
    return {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
        "meta": meta,
    }
```

```python
# utils/exceptions.py

from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, AuthenticationFailed, NotFound
from rest_framework.response import Response
from .response import api_response


def custom_exception_handler(exc, context):
    """
    Global DRF exception handler.

    Wraps ALL error responses in our standard api_response envelope
    so the React frontend always receives the same shape, even for
    unhandled server errors.
    """
    # Let DRF handle the exception first
    response = exception_handler(exc, context)

    if response is not None:
        # DRF handled it — reformat into our envelope
        errors = response.data if isinstance(response.data, dict) else None
        message = _extract_message(exc, response.data)

        response.data = api_response(
            success=False,
            message=message,
            errors=errors,
        )
    else:
        # Unhandled exception — return 500 in our envelope
        response = Response(
            api_response(
                success=False,
                message="An unexpected server error occurred. Please contact the administrator.",
            ),
            status=500,
        )

    return response


def _extract_message(exc, data):
    """Extract a human-readable message from the exception."""
    if isinstance(exc, ValidationError):
        return "Validation failed. Please check the provided data."
    if isinstance(exc, AuthenticationFailed):
        return "Authentication failed. Please log in again."
    if isinstance(exc, NotFound):
        return "The requested resource was not found."
    # Fall back to first error in the response body
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    return "Request failed."
```

```python
# utils/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .response import api_response


class StandardResultsPagination(PageNumberPagination):
    """
    Custom paginator that wraps list results in our api_response envelope
    and includes pagination metadata in the `meta` field.

    Response shape for paginated lists:
    {
        "success": true,
        "data": [ ... results ... ],
        "meta": {
            "total": 38,
            "page": 1,
            "page_size": 25,
            "total_pages": 2,
            "has_next": true,
            "has_previous": false
        }
    }
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(api_response(
            success=True,
            data=data,
            meta={
                "total": self.page.paginator.count,
                "page": self.page.number,
                "page_size": self.get_page_size(self.request),
                "total_pages": self.page.paginator.num_pages,
                "has_next": self.page.has_next(),
                "has_previous": self.page.has_previous(),
            }
        ))
```

---

## 12. Custom Permissions Matrix

```python
# utils/permissions.py

from rest_framework.permissions import BasePermission
from apps.accounts.models import Role


class IsAdmin(BasePermission):
    """
    Allows access only to users with the ADMIN role.
    Used for: user management, system configuration, institution settings.
    """
    message = "Access restricted to administrators only."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == Role.ADMIN
        )


class IsAdminOrOfficer(BasePermission):
    """
    Allows access to ADMIN and OFFICER roles.
    Used for: case management, student profiles, reports, audit log.
    """
    message = "Access restricted to officers and administrators."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.OFFICER)
        )


class IsAdminOrOfficerOrStaff(BasePermission):
    """
    Allows access to all authenticated roles.
    Used for: creating new case reports (Staff can file incidents),
    reading students (for form lookups).
    Staff cannot UPDATE, DELETE, or TRANSITION cases — that's handled
    in the view's get_permissions() method.
    """
    message = "You must be logged in to access this resource."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: only the user who created the resource
    or an admin can modify it.
    Used for: case notes (officer can only edit their own notes).
    """
    message = "You do not have permission to modify this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == Role.ADMIN:
            return True
        # Check if the object has a `created_by` or `reported_by` field
        owner = getattr(obj, "created_by", None) or getattr(obj, "reported_by", None)
        return owner == request.user
```

**Permission matrix by role:**

| Endpoint | Admin | Officer | Staff |
|---|:---:|:---:|:---:|
| Login / Refresh | ✅ | ✅ | ✅ |
| List / Search Students | ✅ | ✅ | ✅ |
| Create Student | ✅ | ✅ | ❌ |
| Update / Deactivate Student | ✅ | ✅ | ❌ |
| Biometric Enroll | ✅ | ✅ | ❌ |
| Biometric Verify | ✅ | ✅ | ✅ |
| Create Case (file report) | ✅ | ✅ | ✅ |
| View Case Details | ✅ | ✅ | Own cases only |
| Update Case | ✅ | ✅ | ❌ |
| Transition Case Status | ✅ | ✅ | ❌ |
| Upload Case Documents | ✅ | ✅ | ✅ |
| View Reports / Dashboard | ✅ | ✅ | ❌ |
| Export PDF / CSV | ✅ | ✅ | ❌ |
| View Audit Log | ✅ | Read-only | ❌ |
| User Admin | ✅ | ❌ | ❌ |

---

## 13. URL Routing

```python
# config/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Django admin — restricted to is_staff users
    path("admin/", admin.site.urls),

    # API v1 — all app routes are namespaced under /api/
    path("api/", include("config.api_urls")),

    # OpenAPI schema + Swagger UI for development
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
```

```python
# config/api_urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, MeView, UserListCreateView, UserDetailView
from apps.students.views import StudentViewSet
from apps.biometric.views import BiometricEnrollView, BiometricVerifyView
from apps.cases.views import DisciplinaryCaseViewSet
from apps.reports.views import DashboardStatsView
from apps.audit.views import AuditLogListView

# DRF router auto-generates list/detail/custom-action URLs for ViewSets
router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="students")
router.register(r"cases", DisciplinaryCaseViewSet, basename="cases")

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────────────
    path("auth/login/",   LoginView.as_view(),        name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(),  name="token_refresh"),
    path("auth/me/",      MeView.as_view(),            name="me"),

    # ── Users (Admin only) ────────────────────────────────────────────
    path("users/",        UserListCreateView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(),   name="user_detail"),

    # ── Biometric ─────────────────────────────────────────────────────
    path("biometric/enroll/", BiometricEnrollView.as_view(), name="biometric_enroll"),
    path("biometric/verify/", BiometricVerifyView.as_view(), name="biometric_verify"),

    # ── Students + Cases (router) ─────────────────────────────────────
    path("", include(router.urls)),

    # ── Reports ───────────────────────────────────────────────────────
    path("reports/dashboard/", DashboardStatsView.as_view(), name="dashboard_stats"),

    # ── Audit Log ─────────────────────────────────────────────────────
    path("audit/", AuditLogListView.as_view(), name="audit_log"),
]
```

---

## 14. Middleware Stack

```python
# middleware/audit_middleware.py

import time
from apps.audit.models import AuditLog


class RequestAuditMiddleware:
    """
    Logs every non-GET request to the audit log automatically.

    POST/PUT/PATCH/DELETE requests represent state changes — they are
    recorded here with the user, path, status code, and response time.
    GET requests are NOT logged here (too noisy; reads are logged only
    when specifically triggered in views, e.g. report exports).

    This middleware is a safety net. Even if a developer forgets to call
    log_action() in a view, mutations are still recorded.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = int((time.time() - start_time) * 1000)

        # Only log mutating requests
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            user = request.user if request.user.is_authenticated else None
            AuditLog.objects.create(
                user=user,
                action=AuditLog.Action.CASE_UPDATE,  # Generic fallback action
                description=f"{request.method} {request.path} → {response.status_code} ({duration_ms}ms)",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )

        return response

    def _get_client_ip(self, request):
        """Get real client IP, accounting for proxies and load balancers."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
```

---

## 15. Environment & Dependencies

### `.env.example`
```bash
# Core Django
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here
DJANGO_SETTINGS_MODULE=config.settings.development
DEBUG=True

# Database (PostgreSQL)
DATABASE_URL=postgres://disciplinetrack_user:password@localhost:5432/disciplinetrack_db

# CORS — React dev server
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Media files storage (production: use S3)
MEDIA_ROOT=/var/www/disciplinetrack/media
MEDIA_URL=/media/
```

### `requirements/base.txt`
```
# Web framework
Django==5.0.*
djangorestframework==3.15.*
djangorestframework-simplejwt==5.3.*

# Database
psycopg2-binary==2.9.*

# Filtering & search
django-filter==24.*

# CORS headers for React frontend
django-cors-headers==4.*

# Environment variables from .env
django-environ==0.11.*

# OpenAPI schema generation (Swagger UI)
drf-spectacular==0.27.*

# Image handling (student photos)
Pillow==10.*

# Production server
gunicorn==22.*
```

### `requirements/development.txt`
```
-r base.txt

# Debug toolbar — see SQL queries, cache hits, etc.
django-debug-toolbar==4.*

# Test data factories
factory-boy==3.*
faker==25.*

# Test runner with coverage
pytest-django==4.*
pytest-cov==5.*
```

---

## 16. Database Schema Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│ TABLE            │ KEY FIELDS                                        │
├─────────────────────────────────────────────────────────────────────┤
│ auth_users       │ id, email (unique), full_name, role, is_active    │
│ departments      │ id, name (unique), code (unique)                  │
│ students         │ id (UUID), reg_number (unique), department_id FK  │
│                  │ biometric_enrolled, is_active, registered_by FK   │
│ biometric_       │ id (UUID), student_id (OneToOne), template_hash   │
│   templates      │ finger_used, enrolled_by FK, enrolled_at          │
│ biometric_verify │ id, student_id FK, result, ip_address, attempted  │
│   _logs          │                                                    │
│ incident_types   │ id, name (unique), severity_default               │
│ disciplinary_    │ id (UUID), case_number (unique), student_id FK    │
│   cases          │ incident_type FK, severity, status, outcome       │
│                  │ reported_by FK, assigned_to FK, decided_by FK     │
│                  │ date_of_incident, description, outcome_notes      │
│ case_documents   │ id, case_id FK, file, original_filename           │
│ case_notes       │ id, case_id FK, body, created_by FK              │
│ audit_logs       │ id, user_id FK, action, resource_type             │
│                  │ resource_id, description, ip_address, timestamp   │
└─────────────────────────────────────────────────────────────────────┘
```

All FKs that reference `students` use `on_delete=PROTECT` — records can never be deleted while cases reference them.

---

## 17. Sprint Build Order

| Sprint | Deliverable | Key files |
|---|---|---|
| 1 | Project scaffold, settings, DB connected | `config/`, `requirements/`, `.env` |
| 2 | `accounts` app — CustomUser, JWT login, RBAC | `apps/accounts/` |
| 3 | `students` app — registration, search, photos | `apps/students/` |
| 4 | `audit` app — AuditLog model, middleware, utils | `apps/audit/` |
| 5 | `biometric` app — enroll + verify endpoints | `apps/biometric/` |
| 6 | `cases` app — models, CRUD, status workflow | `apps/cases/` |
| 7 | `reports` app — dashboard stats, export PDF/CSV | `apps/reports/` |
| 8 | Standard response, pagination, global exception handler | `utils/` |
| 9 | API tests for all apps, CI pipeline | `apps/*/tests/` |
| 10 | Biometric hardware SDK integration (stub → real) | `apps/biometric/` |

---

*Generated from project document: A Secure Biometric System for Monitoring Student Disciplinary and Crime History in Higher Learning Institutions — DIT OD23IT — Supervised by Khalfan Mwarami*
