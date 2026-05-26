"""Biometric API endpoints.

Endpoints:
    POST /api/biometric/enroll/  -> store/update a student's fingerprint hash
    POST /api/biometric/verify/  -> match a live scan hash to a student

The API receives hashes/templates from the scanner integration. It does not
talk directly to USB hardware and does not store raw fingerprint images.
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.students.models import Student
from utils.permissions import IsAdminOrOfficer, IsAdminOrOfficerOrStaff
from utils.response import api_response

from .models import BiometricTemplate, BiometricVerificationLog
from .serializers import BiometricEnrollSerializer, BiometricVerifySerializer


class BiometricEnrollView(APIView):
    permission_classes = [IsAdminOrOfficer]

    def post(self, request):
        serializer = BiometricEnrollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = Student.objects.filter(reg_number=serializer.validated_data["reg_number"]).first()
        if not student:
            return Response(api_response(success=False, message="Student not found"), status=status.HTTP_404_NOT_FOUND)

        BiometricTemplate.objects.update_or_create(
            student=student,
            defaults={
                "template_hash": serializer.validated_data["template_hash"],
                "finger_used": serializer.validated_data.get("finger_used", "right_index"),
                "quality_score": serializer.validated_data.get("quality_score"),
                "enrolled_by": request.user,
                "enrolled_at": timezone.now(),
            },
        )
        student.biometric_enrolled = True
        student.save(update_fields=["biometric_enrolled"])
        return Response(api_response(success=True, message="Student biometric enrolled successfully"))


class BiometricVerifyView(APIView):
    permission_classes = [IsAdminOrOfficerOrStaff]

    def post(self, request):
        serializer = BiometricVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ip = request.META.get("REMOTE_ADDR")
        workstation_id = serializer.validated_data.get("workstation_id", "")

        template = BiometricTemplate.objects.select_related("student", "student__department").filter(
            template_hash=serializer.validated_data["template_hash"]
        ).first()
        if not template:
            BiometricVerificationLog.objects.create(
                result=BiometricVerificationLog.Result.FAILURE,
                ip_address=ip,
                workstation_id=workstation_id,
            )
            return Response(api_response(success=False, message="Fingerprint not recognised"), status=401)

        template.last_verified_at = timezone.now()
        template.save(update_fields=["last_verified_at"])
        BiometricVerificationLog.objects.create(
            student=template.student,
            result=BiometricVerificationLog.Result.SUCCESS,
            ip_address=ip,
            workstation_id=workstation_id,
        )
        student = template.student
        return Response(
            api_response(
                success=True,
                message="Biometric verified",
                data={
                    "student_id": str(student.id),
                    "reg_number": student.reg_number,
                    "full_name": student.full_name,
                    "department": student.department.name,
                },
            )
        )
