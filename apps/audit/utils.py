"""Audit helper functions."""
from .models import AuditLog


def log_action(
    action: str,
    description: str,
    user=None,
    resource_type: str = "",
    resource_id: str = "",
    before_state=None,
    after_state=None,
    ip_address: str = None,
    user_agent: str = "",
) -> AuditLog:
    """Create one audit entry from views, services, signals, or middleware."""
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
