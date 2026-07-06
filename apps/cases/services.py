"""Business logic for case workflow."""
from django.db import transaction
from django.utils import timezone

from apps.notifications.services import send_sms

from .models import DisciplinaryCase

ALLOWED_TRANSITIONS = {
    DisciplinaryCase.Status.REPORTED: [DisciplinaryCase.Status.UNDER_REVIEW],
    DisciplinaryCase.Status.UNDER_REVIEW: [DisciplinaryCase.Status.DECIDED],
    DisciplinaryCase.Status.DECIDED: [DisciplinaryCase.Status.CLOSED],
    DisciplinaryCase.Status.CLOSED: [],
}


def transition_case_status(case: DisciplinaryCase, new_status: str, user, outcome: str = None, outcome_notes: str = ""):
    """Validate and apply a case status transition.

    Views call this function instead of directly changing case.status. This
    keeps the legal workflow rules testable and prevents invalid jumps such as
    REPORTED -> CLOSED.
    """
    allowed_next = ALLOWED_TRANSITIONS.get(case.status, [])
    if new_status not in allowed_next:
        raise ValueError(f"Cannot transition from '{case.status}' to '{new_status}'. Allowed: {allowed_next}")

    with transaction.atomic():
        case.status = new_status
        if new_status == DisciplinaryCase.Status.DECIDED:
            if not outcome:
                raise ValueError("Outcome is required when deciding a case")
            case.outcome = outcome
            case.outcome_notes = outcome_notes
            case.decided_by = user
            case.decided_at = timezone.now()
        case.save()

    if new_status in (DisciplinaryCase.Status.DECIDED, DisciplinaryCase.Status.CLOSED) and case.student.phone:
        send_sms(
            to=case.student.phone,
            message=(
                f"DisciplineTrack: case {case.case_number} has been {new_status.lower()}"
                + (f" — outcome: {case.get_outcome_display()}" if new_status == DisciplinaryCase.Status.DECIDED else "")
                + "."
            ),
            case=case,
        )
    return case
