"""Project paginator used by list endpoints."""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .response import api_response


class StandardResultsPagination(PageNumberPagination):
    """Return paginated results inside the standard API envelope."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            api_response(
                success=True,
                data=data,
                meta={
                    "total": self.page.paginator.count,
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "total_pages": self.page.paginator.num_pages,
                    "has_next": self.page.has_next(),
                    "has_previous": self.page.has_previous(),
                },
            )
        )
