"""Student profile models.

This app owns academic identity and basic profile data. It only stores a
biometric_enrolled flag; the actual fingerprint template lives in biometric.
"""
import uuid

from django.db import models


class Department(models.Model):
    """Academic department used for grouping students and reports."""

    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = "departments"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Student(models.Model):
    """Core student profile.

    UUID primary keys avoid exposing sequential IDs in API URLs. Use reg_number
    for human lookup and reporting.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reg_number = models.CharField(max_length=50, unique=True, db_index=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[("M", "Male"), ("F", "Female"), ("O", "Other")], blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="students")
    academic_year = models.CharField(max_length=20)
    level = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    photo = models.ImageField(upload_to="students/photos/%Y/", null=True, blank=True)
    biometric_enrolled = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    registered_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
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
