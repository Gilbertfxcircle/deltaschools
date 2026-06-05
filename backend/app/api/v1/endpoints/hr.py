"""Staff & HR: staff records + leave (hr_management module)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import Leave, Staff
from app.services.audit import audit_actor_school

router = APIRouter()


class StaffCreate(BaseModel):
    staff_no: str
    full_name: str
    designation: str | None = None
    email: str | None = None


class LeaveCreate(BaseModel):
    staff_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveDecision(BaseModel):
    decision: str  # approved | rejected


@router.get("/staff")
def list_staff(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("staff:read")),
) -> dict:
    rows = db.execute(select(Staff)).scalars().all()
    return ok(
        [{"id": r.id, "staff_no": r.staff_no, "name": r.full_name,
          "designation": r.designation} for r in rows]
    )


@router.post("/staff")
def create_staff(
    payload: StaffCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("staff:write")),
) -> dict:
    row = Staff(
        staff_no=payload.staff_no, full_name=payload.full_name,
        designation=payload.designation, email=payload.email,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="staff",
        resource_id=row.id, new_value={"staff_no": payload.staff_no, "name": payload.full_name},
    )
    db.commit()
    return ok({"id": row.id}, message="Staff created")


@router.post("/leaves")
def request_leave(
    payload: LeaveCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("staff:read")),
) -> dict:
    row = Leave(
        staff_id=payload.staff_id, leave_type=payload.leave_type,
        start_date=payload.start_date, end_date=payload.end_date, reason=payload.reason,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="leaves",
        resource_id=row.id, new_value={"staff_id": payload.staff_id, "type": payload.leave_type},
    )
    db.commit()
    return ok({"id": row.id, "status": row.status}, message="Leave requested")


@router.patch("/leaves/{leave_id}")
def decide_leave(
    leave_id: str,
    payload: LeaveDecision,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("staff:write")),
) -> dict:
    if payload.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="decision must be approved|rejected")
    row = db.get(Leave, leave_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Leave not found")
    row.status = payload.decision
    db.flush()
    audit_actor_school(
        db, actor=actor,
        action=AuditAction.APPROVE if payload.decision == "approved" else AuditAction.REJECT,
        resource="leaves", resource_id=row.id, new_value={"status": payload.decision},
    )
    db.commit()
    return ok({"id": row.id, "status": row.status}, message=f"Leave {row.status}")
