"""SMS provider abstraction.

Add a new provider by subclassing SmsProvider and registering it in
get_provider() below. Swapping providers is then a one-line settings change
(SMS_PROVIDER) — no changes needed anywhere sms is actually sent from.
"""
import logging
from dataclasses import dataclass

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class SmsResult:
    success: bool
    status: str  # SmsLog.Status value
    error: str = ""


class SmsProvider:
    def send(self, to: str, message: str) -> SmsResult:
        raise NotImplementedError


class ConsoleProvider(SmsProvider):
    """Default provider — no real sending, just logs. Safe to use with no credentials."""

    def send(self, to: str, message: str) -> SmsResult:
        logger.info("[sms:console] to=%s message=%r", to, message)
        return SmsResult(success=True, status="LOGGED")


class SendAfricaProvider(SmsProvider):
    """
    SendAfrica (docs.sendafrica.online / api.sendafrica.online) — Tanzania-only SMS.

    Per the official developer guide:
      POST /v1/sms/            auth: X-API-Key header       body: {to, message, from?}
      GET  /v1/credits/balance auth: X-API-Key header

    Only Tanzania mobile numbers (06x/07x, 10 digits) are accepted — the API
    normalises 0712345678 / +255712345678 / 255712345678 itself, but rejects
    anything else with error code "invalid_phone".
    """

    SEND_PATH = "/v1/sms/"
    BALANCE_PATH = "/v1/credits/balance"

    def _headers(self):
        return {"X-API-Key": settings.SENDAFRICA_API_KEY, "Content-Type": "application/json"}

    def send(self, to: str, message: str) -> SmsResult:
        api_key = settings.SENDAFRICA_API_KEY
        if not api_key:
            return SmsResult(success=False, status="FAILED", error="SENDAFRICA_API_KEY is not set")

        try:
            response = requests.post(
                f"{settings.SENDAFRICA_BASE_URL}{self.SEND_PATH}",
                headers=self._headers(),
                json={
                    "to": to,
                    "message": message,
                    **({"from": settings.SENDAFRICA_SENDER_ID} if settings.SENDAFRICA_SENDER_ID else {}),
                },
                timeout=10,
            )
            body = response.json()
        except requests.RequestException as exc:
            logger.warning("[sms:sendafrica] request failed: %s", exc)
            return SmsResult(success=False, status="FAILED", error=str(exc))
        except ValueError:
            return SmsResult(success=False, status="FAILED", error=f"Non-JSON response (HTTP {response.status_code})")

        if body.get("success"):
            data = body.get("data", {})
            logger.info("[sms:sendafrica] sent to=%s message_id=%s status=%s", to, data.get("message_id"), data.get("status"))
            return SmsResult(success=True, status="SENT")

        err = body.get("error", {})
        error_msg = f"{err.get('code', 'unknown_error')}: {err.get('message', 'Send failed')}"
        logger.warning("[sms:sendafrica] send failed to=%s: %s", to, error_msg)
        return SmsResult(success=False, status="FAILED", error=error_msg)

    def check_balance(self):
        """Returns the remaining SMS credit balance, or None if the call fails."""
        try:
            response = requests.get(
                f"{settings.SENDAFRICA_BASE_URL}{self.BALANCE_PATH}",
                headers=self._headers(),
                timeout=10,
            )
            body = response.json()
        except (requests.RequestException, ValueError):
            return None
        if body.get("success"):
            return body.get("data", {}).get("balance")
        return None


def get_provider() -> SmsProvider:
    # Tolerate spelling/casing variants ("sendafrica", "sendAfrika", "send_africa", ...)
    name = "".join(ch for ch in (settings.SMS_PROVIDER or "").lower() if ch.isalpha())
    if name in ("sendafrica", "sendafrika"):
        return SendAfricaProvider()
    return ConsoleProvider()
