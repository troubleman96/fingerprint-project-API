"""Fingerprint enrollment and verification models."""
import uuid

from django.db import models


class BiometricTemplate(models.Model):
    """Fingerprint template reference for one student.

    Security rule: never store raw fingerprint images. Store only a hash of the
    scanner SDK template. The hardware/local agent should produce the template.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.OneToOneField("students.Student", on_delete=models.CASCADE, related_name="biometric_template")
    template_hash = models.CharField(max_length=64, unique=True)
    finger_used = models.CharField(max_length=20, default="right_index")
    quality_score = models.FloatField(null=True, blank=True)
    enrolled_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enrolled_biometrics",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    last_verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "biometric_templates"

    def __str__(self):
        return f"Template for {self.student.reg_number}"


class BiometricVerificationLog(models.Model):
    """Every verification attempt, successful or failed."""

    class Result(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        ERROR = "ERROR", "Scanner Error"

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verification_attempts",
    )
    result = models.CharField(max_length=10, choices=Result.choices)
    match_score = models.FloatField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    workstation_id = models.CharField(max_length=100, blank=True)
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "biometric_verification_logs"
        indexes = [
            models.Index(fields=["student", "attempted_at"]),
            models.Index(fields=["result"]),
        ]
