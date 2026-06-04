"""Read-only audit log endpoints (section 9 ``/audit``).

There is deliberately NO write/update/delete route here. Audit records are
created by the audit service as a side effect of other writes, and immutability
is enforced by the database trigger (LAW #4).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.response import ok
from app.models.school_models import SchoolAuditLog

router = APIRouter()


@router.get("")
def list_audit(
    request: Request,
    limit: int = 100,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("audit:read")),
) -> dict:
    """Return recent audit entries for the current tenant (read-only)."""
    limit = max(1, min(limit, 500))
    rows = (
        db.execute(select(SchoolAuditLog).order_by(SchoolAuditLog.timestamp.desc()).limit(limit))
        .scalars()
        .all()
    )
    data = [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "user_email": r.user_email,
            "action": r.action,
            "resource": r.resource,
            "resource_id": r.resource_id,
            "approval_status": r.approval_status,
        }
        for r in rows
    ]
    return ok(data)
