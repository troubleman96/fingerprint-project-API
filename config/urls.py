"""Project URL dispatcher.

All API endpoints live under /api/. Human-friendly API documentation is
available at /api/docs/ when drf-spectacular is installed.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from .docs import local_api_docs

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("config.api_urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", local_api_docs, name="api-docs"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
