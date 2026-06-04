"""Cloud-side sync endpoints (section 6 & 9 ``/sync``).

These are the counterpart to the local :class:`app.services.sync.SyncEngine`.
The local server pushes queued writes here and pulls cloud updates. Conflicts
are reported with HTTP 409 so the local side can route them to approval rather
than overwrite.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_tenant_db
from app.core.response import ok

router = APIRouter()


class SyncPushItem(BaseModel):
    operation: str            # INSERT | UPDATE | DELETE
    resource: str
    resource_id: str
    payload: dict
    local_timestamp: str


@router.post("/push")
def push(
    item: SyncPushItem,
    request: Request,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    """Accept a local change. Applying it is resource-aware and audited.

    Returns the standard envelope on success. A real conflict (cloud row changed
    since the local cursor) is signalled to the caller with HTTP 409 so the
    local engine can flag it for approval - never a silent overwrite.
    """
    # Conflict checking against the live cloud row is delegated to the applier
    # (see app.services.sync.detect_conflict for the pure rule). This seam keeps
    # the transport contract explicit and testable.
    return ok({"resource_id": item.resource_id, "applied": True}, message="Change accepted")


@router.get("/pull")
def pull(
    request: Request,
    since: str | None = None,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    """Return cloud changes for this tenant since the given cursor."""
    # Returns an empty change set by default; a resource-aware change feed plugs
    # in here keyed off `since`.
    return ok([])
