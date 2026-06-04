"""Module enable/disable + discovery (section 7 & 9)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_db, require_super_admin
from app.core.modules import AVAILABLE_MODULES, is_valid_module
from app.core.response import ok
from app.models.global_models import InstitutionModule

router = APIRouter()


@router.get("/available")
def available_modules() -> dict:
    """Return the canonical registry of modules that can be enabled."""
    return ok(sorted(AVAILABLE_MODULES))


@router.get("/enabled")
def enabled_modules(request: Request, db: Session = Depends(get_db)) -> dict:
    """Return the modules enabled for the current tenant.

    The frontend renders navigation strictly from this list - disabled modules
    are invisible (section 7).
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not identified")
    rows = db.execute(
        select(InstitutionModule).where(
            InstitutionModule.tenant_id == tenant_id, InstitutionModule.enabled.is_(True)
        )
    ).scalars().all()
    return ok(sorted(r.module_key for r in rows))


@router.post("/{tenant_id}/{module_key}/enable")
def enable_module(
    tenant_id: str,
    module_key: str,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_super_admin),
) -> dict:
    """Enable a module for an institution (super admin only)."""
    if not is_valid_module(module_key):
        raise HTTPException(status_code=400, detail=f"Unknown module: {module_key}")
    row = db.execute(
        select(InstitutionModule).where(
            InstitutionModule.tenant_id == tenant_id,
            InstitutionModule.module_key == module_key,
        )
    ).scalar_one_or_none()
    if row is None:
        row = InstitutionModule(tenant_id=tenant_id, module_key=module_key, enabled=True)
        db.add(row)
    else:
        row.enabled = True
    db.commit()
    return ok(message=f"Module '{module_key}' enabled for {tenant_id}")
