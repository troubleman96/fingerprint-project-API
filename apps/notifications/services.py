"""Entry point for sending SMS. Callers (case creation, status changes, ...)
should only ever call send_sms() — it never raises, so a notification
failure can't break the case workflow that triggered it.
"""
import logging

from .models import SmsLog
from .providers import get_provider

logger = logging.getLogger(__name__)


def send_sms(to: str, message: str, case=None) -> SmsLog:
    provider = get_provider()
    provider_name = provider.__class__.__name__

    try:
        result = provider.send(to, message)
        status, error = result.status, result.error
    except Exception as exc:  # provider bugs shouldn't break the caller either
        logger.exception("[sms] unexpected provider error")
        status, error = SmsLog.Status.FAILED, str(exc)

    return SmsLog.objects.create(
        recipient=to,
        message=message,
        provider=provider_name,
        status=status,
        error=error,
        case=case,
    )


def check_sms_balance():
    """Returns the SMS credit balance for providers that support it, else None."""
    provider = get_provider()
    check = getattr(provider, "check_balance", None)
    return check() if check else None
