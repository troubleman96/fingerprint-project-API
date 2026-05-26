from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import CustomUser, Role
from apps.cases.models import DisciplinaryCase, IncidentType
from apps.students.models import Department, Student


class ApiEndpointSmokeTests(TestCase):
    """End-to-end smoke tests for the main API surface.

    These tests intentionally use HTTP requests through DRF's APIClient rather
    than calling views/services directly. That catches routing, permissions,
    serializers, response shapes, and model wiring together.
    """

    def setUp(self):
        self.client = APIClient()
        self.admin = CustomUser.objects.create_user(
            email="admin@example.com",
            password="StrongPass123",
            full_name="System Admin",
            role=Role.ADMIN,
            is_staff=True,
        )
        self.officer = CustomUser.objects.create_user(
            email="officer@example.com",
            password="StrongPass123",
            full_name="Case Officer",
            role=Role.OFFICER,
        )
        self.client.force_authenticate(self.admin)

        self.department = Department.objects.create(name="Computer Studies", code="CS")
        self.student = Student.objects.create(
            reg_number="220229358370",
            first_name="Asha",
            last_name="Salim",
            department=self.department,
            academic_year="2025/2026",
            registered_by=self.admin,
        )
        self.incident_type = IncidentType.objects.create(name="Academic Fraud", severity_default="HIGH")

    def test_auth_login_and_me_endpoints_work(self):
        anonymous = APIClient()
        login_response = anonymous.post(
            "/api/auth/login/",
            {"email": "admin@example.com", "password": "StrongPass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("access", login_response.data)
        self.assertEqual(login_response.data["user"]["role"], Role.ADMIN)

        refresh_response = anonymous.post(
            "/api/auth/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)

        me_response = self.client.get("/api/auth/me/")
        self.assertEqual(me_response.status_code, 200)
        self.assertTrue(me_response.data["success"])
        self.assertEqual(me_response.data["data"]["email"], "admin@example.com")

        schema_response = anonymous.get("/api/schema/")
        self.assertEqual(schema_response.status_code, 200)

    def test_user_admin_endpoints_work(self):
        create_response = self.client.post(
            "/api/users/",
            {
                "email": "staff@example.com",
                "full_name": "Registry Staff",
                "role": Role.STAFF,
                "department": "Registry",
                "phone": "255700000001",
                "password": "StrongPass123",
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        user_id = create_response.data["data"]["id"]

        list_response = self.client.get("/api/users/")
        self.assertEqual(list_response.status_code, 200)

        detail_response = self.client.get(f"/api/users/{user_id}/")
        self.assertEqual(detail_response.status_code, 200)

        deactivate_response = self.client.delete(f"/api/users/{user_id}/")
        self.assertEqual(deactivate_response.status_code, 200)

    def test_department_and_student_endpoints_work(self):
        department_response = self.client.post(
            "/api/departments/",
            {"name": "Business Administration", "code": "BA"},
            format="json",
        )
        self.assertEqual(department_response.status_code, 201)
        department_id = department_response.data["id"]

        department_detail_response = self.client.get(f"/api/departments/{department_id}/")
        self.assertEqual(department_detail_response.status_code, 200)

        student_response = self.client.post(
            "/api/students/",
            {
                "reg_number": "230000000001",
                "first_name": "Juma",
                "last_name": "Musa",
                "gender": "M",
                "department_id": self.department.id,
                "academic_year": "2025/2026",
                "level": "NTA Level 6",
            },
            format="json",
        )
        self.assertEqual(student_response.status_code, 201)
        student_id = student_response.data["id"]

        list_response = self.client.get("/api/students/?search=Juma")
        self.assertEqual(list_response.status_code, 200)
        self.assertTrue(list_response.data["success"])

        detail_response = self.client.get(f"/api/students/{student_id}/")
        self.assertEqual(detail_response.status_code, 200)

        cases_response = self.client.get(f"/api/students/{student_id}/cases/")
        self.assertEqual(cases_response.status_code, 200)

    def test_biometric_enroll_and_verify_endpoints_work(self):
        template_hash = "a" * 64
        enroll_response = self.client.post(
            "/api/biometric/enroll/",
            {
                "reg_number": self.student.reg_number,
                "template_hash": template_hash,
                "finger_used": "right_index",
                "quality_score": 0.95,
            },
            format="json",
        )
        self.assertEqual(enroll_response.status_code, 200)

        verify_response = self.client.post(
            "/api/biometric/verify/",
            {"template_hash": template_hash, "workstation_id": "terminal-01"},
            format="json",
        )
        self.assertEqual(verify_response.status_code, 200)
        self.assertEqual(verify_response.data["data"]["reg_number"], self.student.reg_number)

        failed_response = self.client.post(
            "/api/biometric/verify/",
            {"template_hash": "b" * 64, "workstation_id": "terminal-01"},
            format="json",
        )
        self.assertEqual(failed_response.status_code, 401)

    def test_case_workflow_notes_documents_and_reports_work(self):
        create_response = self.client.post(
            "/api/cases/",
            {
                "student": str(self.student.id),
                "incident_type": self.incident_type.id,
                "severity": DisciplinaryCase.Severity.HIGH,
                "description": "Student submitted copied assignment.",
                "date_of_incident": "2026-05-20",
                "location": "Lab 2",
                "assigned_to": self.officer.id,
            },
            format="json",
        )
        self.assertEqual(create_response.status_code, 201)
        case_id = create_response.data["id"]

        list_response = self.client.get("/api/cases/?status=REPORTED")
        self.assertEqual(list_response.status_code, 200)

        transition_response = self.client.post(
            f"/api/cases/{case_id}/transition/",
            {"status": DisciplinaryCase.Status.UNDER_REVIEW},
            format="json",
        )
        self.assertEqual(transition_response.status_code, 200)

        decide_response = self.client.post(
            f"/api/cases/{case_id}/transition/",
            {
                "status": DisciplinaryCase.Status.DECIDED,
                "outcome": DisciplinaryCase.Outcome.WARNING,
                "outcome_notes": "Formal warning issued.",
            },
            format="json",
        )
        self.assertEqual(decide_response.status_code, 200)

        note_response = self.client.post(
            f"/api/cases/{case_id}/notes/",
            {"body": "Reviewed evidence with department head."},
            format="json",
        )
        self.assertEqual(note_response.status_code, 201)

        notes_list_response = self.client.get(f"/api/cases/{case_id}/notes/")
        self.assertEqual(notes_list_response.status_code, 200)

        document = SimpleUploadedFile("evidence.txt", b"sample evidence", content_type="text/plain")
        document_response = self.client.post(
            f"/api/cases/{case_id}/documents/",
            {"file": document, "description": "Evidence note"},
            format="multipart",
        )
        self.assertEqual(document_response.status_code, 201)

        documents_list_response = self.client.get(f"/api/cases/{case_id}/documents/")
        self.assertEqual(documents_list_response.status_code, 200)

        case_detail_response = self.client.get(f"/api/cases/{case_id}/")
        self.assertEqual(case_detail_response.status_code, 200)

        report_response = self.client.get("/api/reports/dashboard/")
        self.assertEqual(report_response.status_code, 200)
        self.assertIn("headline", report_response.data["data"])

    def test_audit_endpoint_works(self):
        response = self.client.get("/api/audit/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])
