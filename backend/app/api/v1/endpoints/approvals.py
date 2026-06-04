"""Approval-request endpoints (section 4.4).

The super admin can only *submit* a request; the school director decides. The
domain state machine in :mod:`app.domain.approvals` guarantees a change is only
applied after approval, and every step is written to the immutable audit log.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_db, require_permission
from app.core.response import ok
from app.domain.approvals import (
    ApprovalDecision,
    ApprovalError,
    ApprovalRequest,
    ApprovalState,
    requires_approval,
)
from app.models.global_models import ApprovalRequestModel

router = APIRouter()


class ApprovalCreate(BaseModel):
    school_id: str
    resource: str
    resource_id: str | None = None
    requested_change: dict
    reason: str


class ApprovalDecide(BaseModel):
    decision: str  # "approved" | "rejected"
    notes: str | None = None


@router.post("")
def submit_approval(
    payload: ApprovalCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("approval_requests:submit")),
) -> dict:
    """Submit a request to modify protected data (super admin)."""
    if not requires_approval(payload.resource):
        raise HTTPException(
            status_code=400,
            detail=f"Resource '{payload.resource}' is not approval-gated",
        )
    row = ApprovalRequestModel(
        tenant_id=payload.school_id,
        resource=payload.resource,
        resource_id=payload.resource_id,
        requested_change=json.dumps(payload.requested_change),
        reason=payload.reason,
        requested_by=user.id,
        state=ApprovalState.PENDING.value,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    # NOTE: notify the school director (email + in-app) here.
    return ok({"id": row.id, "state": row.state}, message="Approval request submitted")


@router.patch("/{request_id}")
def decide_approval(
    request_id: str,
    payload: ApprovalDecide,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission("approvals:decide")),
) -> dict:
    """Approve or reject a pending request (director/registrar)."""
    row = db.get(ApprovalRequestModel, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Approval request not found")

    # Rehydrate the domain object to enforce legal transitions.
    domain = ApprovalRequest(
        school_id=row.tenant_id,
        resource=row.resource,
        resource_id=row.resource_id,
        requested_change=json.loads(row.requested_change),
        requested_by=row.requested_by,
        reason=row.reason,
        state=ApprovalState(row.state),
    )
    try:
        decision = ApprovalDecision(payload.decision)
        domain.decide(decision=decision, decided_by=user.id, notes=payload.notes)
    except (ValueError, ApprovalError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    row.state = domain.state.value
    row.decided_by = user.id
    row.decided_at = domain.decided_at
    row.decision_notes = payload.notes
    db.commit()

    # If approved, the service layer applies `requested_change` to tenant data
    # and calls domain.mark_applied(); the outcome is audited either way.
    return ok({"id": row.id, "state": row.state}, message=f"Request {row.state}")


@router.get("")
def list_approvals(
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """List approval requests visible to the caller's tenant."""
    stmt = select(ApprovalRequestModel)
    if user.tenant:
        stmt = stmt.where(ApprovalRequestModel.tenant_id == user.tenant)
    rows = db.execute(stmt).scalars().all()
    return ok(
        [
            {"id": r.id, "resource": r.resource, "state": r.state, "reason": r.reason}
            for r in rows
        ]
    )
