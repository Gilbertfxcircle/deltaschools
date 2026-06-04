"""Student endpoints - demonstrates tenant-scoped, RBAC-guarded writes.

Reads/writes go through a tenant-pinned session, so a token for School A can
never touch School B's rows. National IDs are encrypted at rest (AES-256).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.core.security import encrypt_field
from app.models.school_models import Student
from app.services.audit import audit_actor_school

router = APIRouter()


class StudentCreate(BaseModel):
    admission_no: str
    first_name: str
    last_name: str
    gender: str | None = None
    national_id: str | None = None


@router.get("")
def list_students(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("students:read")),
) -> dict:
    """List students for the current tenant only."""
    rows = db.execute(select(Student).where(Student.is_active.is_(True))).scalars().all()
    data = [
        {
            "id": r.id,
            "admission_no": r.admission_no,
            "name": f"{r.first_name} {r.last_name}",
            "gender": r.gender,
        }
        for r in rows
    ]
    return ok(data)


@router.post("")
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("students:write")),
) -> dict:
    """Create a student in the current tenant's schema (national ID encrypted)."""
    student = Student(
        admission_no=payload.admission_no,
        first_name=payload.first_name,
        last_name=payload.last_name,
        gender=payload.gender,
        national_id_enc=encrypt_field(payload.national_id) if payload.national_id else None,
    )
    db.add(student)
    db.flush()

    # Every write audits before returning (section 16). national_id is never
    # placed in the audit payload in cleartext.
    audit_actor_school(
        db,
        actor=actor,
        action=AuditAction.CREATE,
        resource="students",
        resource_id=student.id,
        new_value={
            "admission_no": payload.admission_no,
            "name": f"{payload.first_name} {payload.last_name}",
        },
    )
    db.commit()
    db.refresh(student)
    return ok({"id": student.id}, message="Student created")
