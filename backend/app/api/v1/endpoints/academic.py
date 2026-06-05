"""Academic endpoints: classes, subjects, enrollments (academic module)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import Enrollment, SchoolClass, Subject
from app.services.audit import audit_actor_school

router = APIRouter()


class ClassCreate(BaseModel):
    name: str
    academic_year: str


class SubjectCreate(BaseModel):
    code: str
    name: str


class EnrollmentCreate(BaseModel):
    student_id: str
    class_id: str
    academic_year: str


@router.get("/classes")
def list_classes(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("academic:read")),
) -> dict:
    rows = db.execute(select(SchoolClass)).scalars().all()
    return ok([{"id": r.id, "name": r.name, "academic_year": r.academic_year} for r in rows])


@router.post("/classes")
def create_class(
    payload: ClassCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("academic:write")),
) -> dict:
    row = SchoolClass(name=payload.name, academic_year=payload.academic_year)
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="classes",
        resource_id=row.id, new_value={"name": payload.name},
    )
    db.commit()
    return ok({"id": row.id}, message="Class created")


@router.get("/subjects")
def list_subjects(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("academic:read")),
) -> dict:
    rows = db.execute(select(Subject)).scalars().all()
    return ok([{"id": r.id, "code": r.code, "name": r.name} for r in rows])


@router.post("/subjects")
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("academic:write")),
) -> dict:
    row = Subject(code=payload.code, name=payload.name)
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="subjects",
        resource_id=row.id, new_value={"code": payload.code, "name": payload.name},
    )
    db.commit()
    return ok({"id": row.id}, message="Subject created")


@router.post("/enrollments")
def create_enrollment(
    payload: EnrollmentCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("enrollments:write")),
) -> dict:
    row = Enrollment(
        student_id=payload.student_id,
        class_id=payload.class_id,
        academic_year=payload.academic_year,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="enrollments",
        resource_id=row.id, new_value=payload.model_dump(),
    )
    db.commit()
    return ok({"id": row.id}, message="Enrollment created")
