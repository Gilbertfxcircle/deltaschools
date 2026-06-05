"""E-learning courses + lessons (lms module)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import LmsCourse, LmsLesson
from app.services.audit import audit_actor_school

router = APIRouter()


class CourseCreate(BaseModel):
    title: str
    subject_id: str | None = None
    description: str | None = None


class LessonCreate(BaseModel):
    course_id: str
    title: str
    content_url: str | None = None
    position: int = 0


@router.get("/courses")
def list_courses(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("lms:read")),
) -> dict:
    rows = db.execute(select(LmsCourse)).scalars().all()
    return ok([{"id": r.id, "title": r.title, "description": r.description} for r in rows])


@router.post("/courses")
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("lms:write")),
) -> dict:
    row = LmsCourse(
        title=payload.title, subject_id=payload.subject_id,
        description=payload.description, teacher_id=actor.id,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="lms_courses",
        resource_id=row.id, new_value={"title": payload.title},
    )
    db.commit()
    return ok({"id": row.id}, message="Course created")


@router.get("/courses/{course_id}/lessons")
def list_lessons(
    course_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("lms:read")),
) -> dict:
    rows = (
        db.execute(
            select(LmsLesson).where(LmsLesson.course_id == course_id).order_by(LmsLesson.position)
        )
        .scalars()
        .all()
    )
    return ok(
        [
            {"id": r.id, "title": r.title, "content_url": r.content_url, "position": r.position}
            for r in rows
        ]
    )


@router.post("/lessons")
def create_lesson(
    payload: LessonCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("lms:write")),
) -> dict:
    row = LmsLesson(
        course_id=payload.course_id, title=payload.title,
        content_url=payload.content_url, position=payload.position,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="lms_lessons",
        resource_id=row.id, new_value={"title": payload.title},
    )
    db.commit()
    return ok({"id": row.id}, message="Lesson created")
