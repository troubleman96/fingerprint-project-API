"""Global DRF exception formatting."""
from rest_framework.exceptions import AuthenticationFailed, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .response import api_response


def custom_exception_handler(exc, context):
    """Wrap all DRF errors in the same response shape used by successful APIs."""
    response = exception_handler(exc, context)
    if response is not None:
        response.data = api_response(
            success=False,
            message=_extract_message(exc, response.data),
            errors=response.data if isinstance(response.data, dict) else None,
        )
        return response

    return Response(
        api_response(
            success=False,
            message="An unexpected server error occurred. Please contact the administrator.",
        ),
        status=500,
    )


def _extract_message(exc, data):
    if isinstance(exc, ValidationError):
        return "Validation failed. Please check the provided data."
    if isinstance(exc, AuthenticationFailed):
        return "Authentication failed. Please log in again."
    if isinstance(exc, NotFound):
        return "The requested resource was not found."
    if isinstance(data, dict) and "detail" in data:
        return str(data["detail"])
    return "Request failed."
