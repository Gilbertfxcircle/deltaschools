"""Attendance computation (attendance & biometric_attendance modules).

Pure logic: validate statuses and compute attendance-rate summaries used by
report cards and at-risk analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"


VALID_STATUSES = frozenset(s.value for s in AttendanceStatus)


class AttendanceError(ValueError):
    """Raised on invalid attendance input."""


def normalize_status(raw: str) -> str:
    """Validate and lowercase an attendance status."""
    value = raw.strip().lower()
    if value not in VALID_STATUSES:
        raise AttendanceError(f"Invalid attendance status: {raw!r}")
    return value


@dataclass(frozen=True)
class AttendanceSummary:
    total: int
    present: int
    absent: int
    late: int
    excused: int
    rate: float  # fraction in [0, 1]; present+late+excused counted as "in"


def summarize(statuses: list[str]) -> AttendanceSummary:
    """Summarize attendance statuses into counts + an attendance rate.

    Present, late and excused all count as "attended" for the rate; only
    unexcused absences reduce it.
    """
    counts = {s.value: 0 for s in AttendanceStatus}
    for raw in statuses:
        counts[normalize_status(raw)] += 1
    total = len(statuses)
    attended = counts["present"] + counts["late"] + counts["excused"]
    rate = (attended / total) if total else 0.0
    return AttendanceSummary(
        total=total,
        present=counts["present"],
        absent=counts["absent"],
        late=counts["late"],
        excused=counts["excused"],
        rate=round(rate, 4),
    )
