"""Reporting endpoints (cross-module read-only aggregates)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.response import ok
from app.domain.grading import rank_students
from app.models.school_models import Invoice, ReportCard, Student

router = APIRouter()


@router.get("/finance/summary")
def finance_summary(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("reports:read")),
) -> dict:
    """Total billed vs outstanding across all invoices for the tenant."""
    total_billed = db.execute(select(func.coalesce(func.sum(Invoice.amount), 0))).scalar_one()
    total_outstanding = db.execute(
        select(func.coalesce(func.sum(Invoice.balance), 0))
    ).scalar_one()
    return ok(
        {
            "total_billed": float(total_billed),
            "total_outstanding": float(total_outstanding),
            "total_collected": float(total_billed) - float(total_outstanding),
        }
    )


@router.get("/students/count")
def student_count(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("reports:read")),
) -> dict:
    count = db.execute(
        select(func.count()).select_from(Student).where(Student.is_active.is_(True))
    ).scalar_one()
    return ok({"active_students": int(count)})


@router.get("/exams/{examination_id}/ranking")
def exam_ranking(
    examination_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("reports:read")),
) -> dict:
    """Rank students for an exam using their report-card averages."""
    rows = (
        db.execute(
            select(ReportCard.student_id, ReportCard.average).where(
                ReportCard.examination_id == examination_id
            )
        )
        .all()
    )
    averages = {sid: float(avg) for sid, avg in rows}
    ranking = rank_students(averages)
    return ok([{"student_id": sid, "position": pos} for sid, pos in ranking])
