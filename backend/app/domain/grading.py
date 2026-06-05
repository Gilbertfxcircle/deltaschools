"""Grading / report-card computation (academic & exams modules).

Pure, framework-free logic so it is fully unit-testable. The default is a
configurable band scale; aggregation (average, GPA, ranking) is computed from
raw marks.
"""

from __future__ import annotations

from dataclasses import dataclass


class GradingError(ValueError):
    """Raised on invalid grading input."""


# Default letter-grade bands: (inclusive lower bound, grade, grade point).
# Ordered high -> low. A school can supply its own bands of the same shape.
DEFAULT_BANDS: tuple[tuple[float, str, float], ...] = (
    (80.0, "A", 4.0),
    (70.0, "B", 3.0),
    (60.0, "C", 2.0),
    (50.0, "D", 1.0),
    (0.0, "F", 0.0),
)


def grade_for_score(
    score: float, bands: tuple[tuple[float, str, float], ...] = DEFAULT_BANDS
) -> str:
    """Return the letter grade for a score using the given bands."""
    if score < 0 or score > 100:
        raise GradingError(f"Score out of range [0, 100]: {score}")
    for lower, grade, _gp in bands:
        if score >= lower:
            return grade
    return bands[-1][1]


def grade_point_for_score(
    score: float, bands: tuple[tuple[float, str, float], ...] = DEFAULT_BANDS
) -> float:
    """Return the grade point for a score using the given bands."""
    if score < 0 or score > 100:
        raise GradingError(f"Score out of range [0, 100]: {score}")
    for lower, _grade, gp in bands:
        if score >= lower:
            return gp
    return bands[-1][2]


@dataclass(frozen=True)
class SubjectResult:
    subject: str
    score: float


@dataclass(frozen=True)
class ReportCard:
    student_id: str
    results: tuple[SubjectResult, ...]
    average: float
    total: float
    gpa: float
    overall_grade: str


def compute_report_card(
    student_id: str,
    results: list[SubjectResult],
    bands: tuple[tuple[float, str, float], ...] = DEFAULT_BANDS,
) -> ReportCard:
    """Compute totals, average, GPA and an overall grade for a student.

    Raises:
        GradingError: If there are no results to aggregate.
    """
    if not results:
        raise GradingError("Cannot compute a report card with no subject results")
    total = sum(r.score for r in results)
    average = total / len(results)
    gpa = sum(grade_point_for_score(r.score, bands) for r in results) / len(results)
    return ReportCard(
        student_id=student_id,
        results=tuple(results),
        average=round(average, 2),
        total=round(total, 2),
        gpa=round(gpa, 2),
        overall_grade=grade_for_score(average, bands),
    )


def rank_students(averages: dict[str, float]) -> list[tuple[str, int]]:
    """Rank students by average (desc). Returns (student_id, position) pairs.

    Ties share the same position (standard competition ranking, "1224").
    """
    ordered = sorted(averages.items(), key=lambda kv: kv[1], reverse=True)
    ranking: list[tuple[str, int]] = []
    last_score: float | None = None
    last_pos = 0
    for idx, (sid, score) in enumerate(ordered, start=1):
        if last_score is None or score != last_score:
            last_pos = idx
            last_score = score
        ranking.append((sid, last_pos))
    return ranking
