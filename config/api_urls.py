"""Version 1 API route table.

Use this file when you need to find or add an endpoint. Routers generate the
standard list/detail URLs for ViewSets; explicit path() entries are used for
single-purpose endpoints such as login and dashboard stats.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import LoginView, MeView, UserDetailView, UserListCreateView
from apps.audit.views import AuditLogListView
from apps.biometric.views import BiometricEnrollView, BiometricVerifyView
from apps.cases.views import DisciplinaryCaseViewSet, IncidentTypeViewSet
from apps.notifications.views import SmsBalanceView, SmsLogListView
from apps.reports.views import DashboardStatsView, DataExportView
from apps.students.views import DepartmentViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"departments", DepartmentViewSet, basename="departments")
router.register(r"students", StudentViewSet, basename="students")
router.register(r"cases", DisciplinaryCaseViewSet, basename="cases")
router.register(r"incident-types", IncidentTypeViewSet, basename="incident-types")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("users/", UserListCreateView.as_view(), name="user_list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user_detail"),
    path("biometric/enroll/", BiometricEnrollView.as_view(), name="biometric_enroll"),
    path("biometric/verify/", BiometricVerifyView.as_view(), name="biometric_verify"),
    path("reports/dashboard/", DashboardStatsView.as_view(), name="dashboard_stats"),
    path("reports/export/", DataExportView.as_view(), name="data_export"),
    path("audit/", AuditLogListView.as_view(), name="audit_log"),
    path("notifications/sms-logs/", SmsLogListView.as_view(), name="sms_log_list"),
    path("notifications/balance/", SmsBalanceView.as_view(), name="sms_balance"),
    path("", include(router.urls)),
]
