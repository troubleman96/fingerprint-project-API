"""Immutable audit trail models."""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append-only record of meaningful system activity.

    Do not update or delete these rows from application code. They exist to
    prove who did what, when, from where, and to which resource.
    """

    class Action(models.TextChoices):
        REQUEST_MUTATION = "REQUEST_MUTATION", "Mutating Request"
        LOGIN = "LOGIN", "User Login"
        LOGOUT = "LOGOUT", "User Logout"
        LOGIN_FAILED = "LOGIN_FAILED", "Failed Login Attempt"
        STUDENT_CREATE = "STUDENT_CREATE", "Student Created"
        STUDENT_UPDATE = "STUDENT_UPDATE", "Student Updated"
        STUDENT_DEACTIVATE = "STUDENT_DEACTIVATE", "Student Deactivated"
        BIOMETRIC_ENROLL = "BIOMETRIC_ENROLL", "Biometric Enrolled"
        BIOMETRIC_VERIFY_SUCCESS = "BIOMETRIC_VERIFY_SUCCESS", "Biometric Verified"
        BIOMETRIC_VERIFY_FAIL = "BIOMETRIC_VERIFY_FAIL", "Biometric Failed"
        CASE_CREATE = "CASE_CREATE", "Case Created"
        CASE_UPDATE = "CASE_UPDATE", "Case Updated"
        CASE_STATUS_CHANGE = "CASE_STATUS_CHANGE", "Case Status Changed"
        CASE_DOCUMENT_UPLOAD = "CASE_DOCUMENT_UPLOAD", "Document Uploaded"
        USER_CREATE = "USER_CREATE", "User Account Created"
        USER_DEACTIVATE = "USER_DEACTIVATE", "User Account Deactivated"
        USER_ROLE_CHANGE = "USER_ROLE_CHANGE", "User Role Changed"
        REPORT_EXPORT = "REPORT_EXPORT", "Report Exported"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]

    def __str__(self):
        user_str = self.user.full_name if self.user else "System"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {user_str} - {self.action}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("AuditLog entries cannot be deleted.")
