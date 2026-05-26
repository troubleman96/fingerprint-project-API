"""Request-level audit safety net."""
import time

from apps.audit.models import AuditLog


class RequestAuditMiddleware:
    """Log every mutating request even when a view forgets explicit auditing.

    GET requests are intentionally skipped because they are noisy. Sensitive read
    actions, such as exporting reports, should call apps.audit.utils.log_action()
    directly from the view/service that performs the read.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        duration_ms = int((time.time() - start_time) * 1000)

        if request.method not in ("GET", "HEAD", "OPTIONS"):
            user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
            AuditLog.objects.create(
                user=user,
                action=AuditLog.Action.REQUEST_MUTATION,
                description=f"{request.method} {request.path} -> {response.status_code} ({duration_ms}ms)",
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
