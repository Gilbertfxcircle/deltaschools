"""Payroll endpoints (payroll module). Protected financial data."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.domain.payroll import compute_payslip
from app.models.school_models import Payroll
from app.services.audit import audit_actor_school

router = APIRouter()


class PayrollRun(BaseModel):
    staff_id: str
    period: str
    gross: float
    allowances: float = 0
    other_deductions: float = 0


@router.post("")
def run_payroll(
    payload: PayrollRun,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("payroll:write")),
) -> dict:
    slip = compute_payslip(
        payload.staff_id, payload.gross, payload.allowances, payload.other_deductions
    )
    row = Payroll(
        staff_id=payload.staff_id,
        period=payload.period,
        gross=float(slip.gross),
        paye=float(slip.paye),
        other_deductions=float(slip.other_deductions),
        net=float(slip.net),
        status="computed",
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="payroll",
        resource_id=row.id,
        new_value={"period": payload.period, "gross": float(slip.gross), "net": float(slip.net)},
    )
    db.commit()
    return ok(
        {
            "id": row.id,
            "gross": float(slip.gross),
            "paye": float(slip.paye),
            "net": float(slip.net),
        },
        message="Payroll computed",
    )


@router.get("/staff/{staff_id}")
def staff_payroll(
    staff_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("payroll:read")),
) -> dict:
    rows = db.execute(select(Payroll).where(Payroll.staff_id == staff_id)).scalars().all()
    return ok(
        [
            {"id": r.id, "period": r.period, "gross": float(r.gross), "net": float(r.net),
             "status": r.status}
            for r in rows
        ]
    )
