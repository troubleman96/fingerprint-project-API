"""SMS notification log.

Every send attempt (real or logged-only) is recorded here so admins can see
what was sent, to whom, and whether it actually reached the provider.
"""
from django.db import models


class SmsLog(models.Model):
    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"
        LOGGED = "LOGGED", "Logged only (no provider configured)"

    recipient = models.CharField(max_length=20)
    message = models.TextField()
    provider = models.CharField(max_length=30)
    status = models.CharField(max_length=10, choices=Status.choices)
    error = models.TextField(blank=True)
    case = models.ForeignKey(
        "cases.DisciplinaryCase",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sms_logs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "sms_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient} — {self.status}"
