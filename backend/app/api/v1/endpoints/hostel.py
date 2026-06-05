"""Hostel rooms + allocations (hostel module)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import HostelAllocation, HostelRoom
from app.services.audit import audit_actor_school

router = APIRouter()


class RoomCreate(BaseModel):
    name: str
    capacity: int = 1
    gender: str | None = None


class AllocationCreate(BaseModel):
    room_id: str
    student_id: str
    academic_year: str


@router.get("/rooms")
def list_rooms(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("hostel:read")),
) -> dict:
    rows = db.execute(select(HostelRoom)).scalars().all()
    return ok([{"id": r.id, "name": r.name, "capacity": r.capacity} for r in rows])


@router.post("/rooms")
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("hostel:write")),
) -> dict:
    row = HostelRoom(name=payload.name, capacity=payload.capacity, gender=payload.gender)
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="hostel_rooms",
        resource_id=row.id, new_value={"name": payload.name},
    )
    db.commit()
    return ok({"id": row.id}, message="Room created")


@router.post("/allocations")
def allocate(
    payload: AllocationCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("hostel:write")),
) -> dict:
    room = db.get(HostelRoom, payload.room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    occupied = db.execute(
        select(func.count()).select_from(HostelAllocation).where(
            HostelAllocation.room_id == payload.room_id,
            HostelAllocation.academic_year == payload.academic_year,
        )
    ).scalar_one()
    if occupied >= room.capacity:
        raise HTTPException(status_code=409, detail="Room is at full capacity")
    row = HostelAllocation(
        room_id=payload.room_id, student_id=payload.student_id,
        academic_year=payload.academic_year,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="hostel_allocations",
        resource_id=row.id, new_value=payload.model_dump(),
    )
    db.commit()
    return ok({"id": row.id}, message="Allocation created")
