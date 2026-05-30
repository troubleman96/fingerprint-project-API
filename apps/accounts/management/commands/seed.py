"""Management command to seed the database from mock-data.json.

Usage:
    python manage.py seed            # insert data (skips existing records)
    python manage.py seed --flush    # wipe all seeded tables first, then insert
"""
import hashlib
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from apps.accounts.models import CustomUser
from apps.audit.models import AuditLog
from apps.biometric.models import BiometricTemplate
from apps.cases.models import DisciplinaryCase, IncidentType
from apps.students.models import Department, Student


class Command(BaseCommand):
    help = "Seed database with mock-data.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Delete all seeded data before inserting",
        )

    def handle(self, *args, **options):
        json_path = Path(settings.BASE_DIR) / "mock-data.json"
        with open(json_path) as f:
            data = json.load(f)

        if options["flush"]:
            self._flush()

        dept_map = self._seed_departments(data["departments"])
        user_map = self._seed_users(data["users"])
        type_map = self._seed_incident_types(data["incidentTypes"])
        student_map = self._seed_students(data["students"], dept_map, user_map)
        self._seed_biometrics(data["students"], student_map, user_map)
        self._seed_cases(data["cases"], student_map, type_map, user_map)
        self._seed_audit_logs(data["auditLog"], user_map)

        self.stdout.write(self.style.SUCCESS("\nDatabase seeded successfully."))

    # ------------------------------------------------------------------ flush

    def _flush(self):
        self.stdout.write("Flushing existing data...")
        # Order matters: dependents first, parents last.
        # QuerySet.delete() bypasses the AuditLog model-level delete() guard.
        AuditLog.objects.all().delete()
        BiometricTemplate.objects.all().delete()
        DisciplinaryCase.objects.all().delete()
        Student.objects.all().delete()
        IncidentType.objects.all().delete()
        Department.objects.all().delete()
        CustomUser.objects.all().delete()
        self.stdout.write("  Flushed.\n")

    # -------------------------------------------------------------- seeders

    def _seed_departments(self, rows):
        """Returns {name: Department instance}."""
        self.stdout.write("Seeding departments...")
        dept_map = {}
        for row in rows:
            obj, created = Department.objects.get_or_create(
                name=row["name"],
                defaults={"code": row["code"]},
            )
            dept_map[obj.name] = obj
            self.stdout.write(f"  {'[+]' if created else '[ ]'} {obj.name}")
        return dept_map

    def _seed_users(self, rows):
        """Returns {full_name: CustomUser instance}."""
        self.stdout.write("Seeding users...")
        user_map = {}
        for row in rows:
            if CustomUser.objects.filter(email=row["email"]).exists():
                obj = CustomUser.objects.get(email=row["email"])
                user_map[row["full_name"]] = obj
                self.stdout.write(f"  [ ] {row['full_name']} ({row['role']})")
                continue

            obj = CustomUser.objects.create_user(
                email=row["email"],
                password=row["password"],
                full_name=row["full_name"],
                role=row["role"],
                department=row.get("department", ""),
                phone=row.get("phone", ""),
                is_active=row.get("is_active", True),
            )
            user_map[row["full_name"]] = obj
            self.stdout.write(f"  [+] {row['full_name']} ({row['role']})")
        return user_map

    def _seed_incident_types(self, rows):
        """Returns {name: IncidentType instance}."""
        self.stdout.write("Seeding incident types...")
        type_map = {}
        for row in rows:
            obj, created = IncidentType.objects.get_or_create(
                name=row["name"],
                defaults={"severity_default": row["severity_default"]},
            )
            type_map[obj.name] = obj
            self.stdout.write(f"  {'[+]' if created else '[ ]'} {obj.name}")
        return type_map

    def _seed_students(self, rows, dept_map, user_map):
        """Returns {mock_int_id: Student instance}."""
        self.stdout.write("Seeding students...")
        student_map = {}

        # Use first officer as the registered_by default
        default_registrar = next(
            (u for u in user_map.values() if u.role == "OFFICER"), None
        )

        for row in rows:
            dept = dept_map.get(row["department"])
            if dept is None:
                self.stdout.write(
                    self.style.WARNING(f"  [!] Unknown department '{row['department']}' for student {row['reg_number']} — skipping")
                )
                continue

            if Student.objects.filter(reg_number=row["reg_number"]).exists():
                obj = Student.objects.get(reg_number=row["reg_number"])
                student_map[row["id"]] = obj
                self.stdout.write(f"  [ ] {row['reg_number']} {row['last_name']}, {row['first_name']}")
                continue

            obj = Student.objects.create(
                reg_number=row["reg_number"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                gender=row.get("gender", ""),
                department=dept,
                academic_year=row["academic_year"],
                level=row.get("level", ""),
                phone=row.get("phone", ""),
                email=row.get("email", ""),
                biometric_enrolled=row.get("biometric_enrolled", False),
                is_active=row.get("is_active", True),
                registered_by=default_registrar,
            )
            student_map[row["id"]] = obj
            self.stdout.write(f"  [+] {row['reg_number']} {row['last_name']}, {row['first_name']}")

        return student_map

    def _seed_biometrics(self, rows, student_map, user_map):
        """Creates BiometricTemplate for every student marked biometric_enrolled=true."""
        self.stdout.write("Seeding biometric templates...")
        enroller = next(
            (u for u in user_map.values() if u.role in ("OFFICER", "ADMIN")), None
        )

        for row in rows:
            if not row.get("biometric_enrolled"):
                continue

            student = student_map.get(row["id"])
            if student is None:
                continue

            if BiometricTemplate.objects.filter(student=student).exists():
                self.stdout.write(f"  [ ] {row['reg_number']}")
                continue

            # Deterministic fake hash: sha256 of reg_number
            template_hash = hashlib.sha256(row["reg_number"].encode()).hexdigest()

            BiometricTemplate.objects.create(
                student=student,
                template_hash=template_hash,
                finger_used="right_index",
                quality_score=0.92,
                enrolled_by=enroller,
            )
            self.stdout.write(f"  [+] {row['reg_number']}")

    def _seed_cases(self, rows, student_map, type_map, user_map):
        """Creates DisciplinaryCase rows, resolving all FK references."""
        self.stdout.write("Seeding cases...")

        for row in rows:
            if DisciplinaryCase.objects.filter(case_number=row["case_number"]).exists():
                self.stdout.write(f"  [ ] {row['case_number']}")
                continue

            student = student_map.get(row["student_id"])
            if student is None:
                self.stdout.write(
                    self.style.WARNING(f"  [!] student_id {row['student_id']} not found for {row['case_number']} — skipping")
                )
                continue

            incident_type = type_map.get(row["incident_type"])
            if incident_type is None:
                self.stdout.write(
                    self.style.WARNING(f"  [!] incident_type '{row['incident_type']}' not found for {row['case_number']} — skipping")
                )
                continue

            reported_by = user_map.get(row.get("reported_by"))
            assigned_to = user_map.get(row.get("assigned_to")) if row.get("assigned_to") else None

            case = DisciplinaryCase(
                case_number=row["case_number"],
                student=student,
                incident_type=incident_type,
                severity=row["severity"],
                status=row["status"],
                outcome=row.get("outcome", ""),
                description=row["description"],
                date_of_incident=row["date_of_incident"],
                location=row.get("location", ""),
                reported_by=reported_by,
                assigned_to=assigned_to,
            )
            case.save()

            # Backfill created_at to match mock timestamp
            if row.get("created_at"):
                DisciplinaryCase.objects.filter(pk=case.pk).update(
                    created_at=parse_datetime(row["created_at"])
                )

            self.stdout.write(f"  [+] {row['case_number']} ({row['status']})")

    def _seed_audit_logs(self, rows, user_map):
        """Creates AuditLog entries.

        AuditLog.save() blocks updates (pk already set) but allows inserts.
        We use QuerySet.update() after creation to set the correct timestamp.
        """
        self.stdout.write("Seeding audit logs...")

        for row in rows:
            user = user_map.get(row.get("user"))

            log = AuditLog(
                user=user,
                action=row["action"],
                resource_type=row.get("resource_type", ""),
                resource_id=row.get("resource_id", ""),
                description=row.get("description", ""),
                ip_address=row.get("ip_address"),
            )
            log.save()  # pk is None here, so the immutability guard passes

            # Backfill the timestamp (auto_now_add can't be set via save)
            if row.get("timestamp"):
                AuditLog.objects.filter(pk=log.pk).update(
                    timestamp=parse_datetime(row["timestamp"])
                )

        self.stdout.write(f"  [+] {len(rows)} log entries")
