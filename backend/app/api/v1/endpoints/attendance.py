"""Attendance endpoints (attendance module)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.domain.attendance import normalize_status, summarize
from app.models.school_models import Attendance
from app.services.audit import audit_actor_school

router = APIRouter()


class AttendanceMark(BaseModel):
    student_id: str
    class_id: str
    on_date: date
    status: str


@router.post("")
def mark_attendance(
    payload: AttendanceMark,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("attendance:write")),
) -> dict:
    status_value = normalize_status(payload.status)
    row = Attendance(
        student_id=payload.student_id,
        class_id=payload.class_id,
        on_date=payload.on_date,
        status=status_value,
        recorded_by=actor.id,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="attendance",
        resource_id=row.id, new_value={"student_id": payload.student_id, "status": status_value},
    )
    db.commit()
    return ok({"id": row.id}, message="Attendance recorded")


@router.get("/student/{student_id}/summary")
def student_summary(
    student_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("attendance:read")),
) -> dict:
    rows = (
        db.execute(select(Attendance).where(Attendance.student_id == student_id))
        .scalars()
        .all()
    )
    summary = summarize([r.status for r in rows])
    return ok(
        {
            "student_id": student_id,
            "total": summary.total,
            "present": summary.present,
            "absent": summary.absent,
            "late": summary.late,
            "excused": summary.excused,
            "rate": summary.rate,
        }
    )
