"""Transport routes + assignments (transport module)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import TransportAssignment, TransportRoute
from app.services.audit import audit_actor_school

router = APIRouter()


class RouteCreate(BaseModel):
    name: str
    fee: float = 0
    capacity: int = 0


class AssignmentCreate(BaseModel):
    route_id: str
    student_id: str
    stop_name: str | None = None


@router.get("/routes")
def list_routes(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("transport:read")),
) -> dict:
    rows = db.execute(select(TransportRoute)).scalars().all()
    return ok([{"id": r.id, "name": r.name, "fee": float(r.fee)} for r in rows])


@router.post("/routes")
def create_route(
    payload: RouteCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("transport:write")),
) -> dict:
    row = TransportRoute(name=payload.name, fee=payload.fee, capacity=payload.capacity)
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="transport_routes",
        resource_id=row.id, new_value={"name": payload.name},
    )
    db.commit()
    return ok({"id": row.id}, message="Route created")


@router.get("/assignments")
def list_assignments(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("transport:read")),
) -> dict:
    rows = db.execute(select(TransportAssignment)).scalars().all()
    return ok(
        [
            {
                "id": r.id,
                "route_id": r.route_id,
                "student_id": r.student_id,
                "stop_name": r.stop_name,
            }
            for r in rows
        ]
    )


@router.post("/assignments")
def assign(
    payload: AssignmentCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("transport:write")),
) -> dict:
    row = TransportAssignment(
        route_id=payload.route_id, student_id=payload.student_id, stop_name=payload.stop_name
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="transport_assignments",
        resource_id=row.id, new_value=payload.model_dump(),
    )
    db.commit()
    return ok({"id": row.id}, message="Assignment created")
