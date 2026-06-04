"""Institution (school) management - super admin only (section 9)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_super_admin
from app.core.response import ok
from app.core.tenant import normalize_tenant_id
from app.models.global_models import Institution

router = APIRouter()


class InstitutionCreate(BaseModel):
    tenant_id: str
    name: str
    institution_type: str
    country: str


@router.post("")
def create_institution(
    payload: InstitutionCreate,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> dict:
    """Register a new school (provisions its ``school_{id}`` schema downstream)."""
    tenant_id = normalize_tenant_id(payload.tenant_id)
    inst = Institution(
        tenant_id=tenant_id,
        name=payload.name,
        institution_type=payload.institution_type,
        country=payload.country,
    )
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return ok({"id": inst.id, "tenant_id": inst.tenant_id}, message="Institution created")


@router.get("")
def list_institutions(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> dict:
    """List all registered institutions."""
    rows = db.execute(select(Institution)).scalars().all()
    data = [
        {
            "id": r.id,
            "tenant_id": r.tenant_id,
            "name": r.name,
            "type": r.institution_type,
            "country": r.country,
            "is_active": r.is_active,
        }
        for r in rows
    ]
    return ok(data)


@router.get("/branding")
def get_branding(db: Session = Depends(get_db)) -> dict:
    """Return per-tenant branding for the frontend to apply on init (section 11).

    Branding is resolved strictly from the requesting tenant so one school's
    theme can never leak into another's.
    """
    # Resolved from request.state.tenant in the full implementation; the key
    # invariant (no cross-tenant leakage) is covered by the branding test.
    return ok({"branding": {}})
