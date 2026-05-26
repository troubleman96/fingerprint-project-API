"""Standard API response helpers.

Every endpoint should return this envelope so the frontend can handle success,
validation errors, pagination, and server errors with one predictable shape.
"""
from typing import Any, Optional


def api_response(
    success: bool,
    message: str = "",
    data: Any = None,
    errors: Any = None,
    meta: Optional[dict] = None,
) -> dict:
    return {
        "success": success,
        "message": message,
        "data": data,
        "errors": errors,
        "meta": meta,
    }
