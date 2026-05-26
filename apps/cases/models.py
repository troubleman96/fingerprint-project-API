"""Disciplinary case models and workflow data."""
import uuid

from django.db import models


class IncidentType(models.Model):
    """Configurable lookup table for misconduct/crime categories."""

    name = models.CharField(max_length=100, unique=True)
    severity_default = models.CharField(
        max_length=10,
        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")],
        default="MEDIUM",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "incident_types"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DisciplinaryCase(models.Model):
    """One disciplinary incident for one student.

    Cases move through REPORTED -> UNDER_REVIEW -> DECIDED -> CLOSED. Use
    services.transition_case_status() for workflow changes so validation and
    side effects stay in one place.
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
        REFERRED = "REFERRED", "Referred to Police"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_number = models.CharField(max_length=50, unique=True, db_index=True, blank=True)
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="disciplinary_cases")
    incident_type = models.ForeignKey(IncidentType, on_delete=models.PROTECT, related_name="cases")
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.REPORTED)
    outcome = models.CharField(max_length=20, choices=Outcome.choices, blank=True)
    description = models.TextField()
    date_of_incident = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    reported_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_cases",
    )
    assigned_to = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_cases",
    )
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
        return f"{self.case_number} - {self.student.reg_number}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            self.case_number = self._generate_case_number()
        super().save(*args, **kwargs)

    def _generate_case_number(self):
        from django.utils import timezone

        year = timezone.now().year
        count = DisciplinaryCase.objects.filter(created_at__year=year).count() + 1
        return f"DIT-{year}-{count:04d}"


class CaseDocument(models.Model):
    """Evidence file attached to a case."""

    case = models.ForeignKey(DisciplinaryCase, on_delete=models.CASCADE, related_name="documents")
    file = models.FileField(upload_to="cases/documents/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True)
    uploaded_by = models.ForeignKey("accounts.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_documents"

    def __str__(self):
        return f"{self.original_filename} -> {self.case.case_number}"


class CaseNote(models.Model):
    """Internal review note visible to officers/admins."""

    case = models.ForeignKey(DisciplinaryCase, on_delete=models.CASCADE, related_name="notes")
    body = models.TextField()
    created_by = models.ForeignKey("accounts.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "case_notes"
        ordering = ["-created_at"]
