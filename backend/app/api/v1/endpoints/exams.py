"""Examinations, marks and report cards (exams module).

Marks are protected data: teachers/dept heads may record them, and report cards
are generated from them using the pure grading logic.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.domain.grading import SubjectResult, compute_report_card, grade_for_score
from app.models.school_models import Examination, Mark, ReportCard, Subject
from app.services.audit import audit_actor_school

router = APIRouter()


class ExamCreate(BaseModel):
    name: str
    academic_year: str
    term: str | None = None


class MarkCreate(BaseModel):
    examination_id: str
    student_id: str
    subject_id: str
    score: float


@router.get("")
def list_exams(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("exams:read")),
) -> dict:
    rows = db.execute(select(Examination)).scalars().all()
    return ok(
        [
            {"id": r.id, "name": r.name, "academic_year": r.academic_year, "term": r.term}
            for r in rows
        ]
    )


@router.get("/marks/{examination_id}")
def list_marks(
    examination_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("marks:read")),
) -> dict:
    rows = (
        db.execute(select(Mark).where(Mark.examination_id == examination_id)).scalars().all()
    )
    return ok(
        [
            {
                "id": r.id,
                "student_id": r.student_id,
                "subject_id": r.subject_id,
                "score": float(r.score),
                "grade": r.grade,
            }
            for r in rows
        ]
    )


@router.post("")
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("exams:write")),
) -> dict:
    row = Examination(name=payload.name, academic_year=payload.academic_year, term=payload.term)
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="examinations",
        resource_id=row.id, new_value={"name": payload.name},
    )
    db.commit()
    return ok({"id": row.id}, message="Examination created")


@router.post("/marks")
def record_mark(
    payload: MarkCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("marks:write")),
) -> dict:
    grade = grade_for_score(payload.score)
    row = Mark(
        examination_id=payload.examination_id,
        student_id=payload.student_id,
        subject_id=payload.subject_id,
        score=payload.score,
        grade=grade,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="marks",
        resource_id=row.id,
        new_value={"student_id": payload.student_id, "score": payload.score, "grade": grade},
    )
    db.commit()
    return ok({"id": row.id, "grade": grade}, message="Mark recorded")


@router.post("/report-cards/{examination_id}/{student_id}")
def generate_report_card(
    examination_id: str,
    student_id: str,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("reports:write")),
) -> dict:
    marks = (
        db.execute(
            select(Mark, Subject)
            .join(Subject, Subject.id == Mark.subject_id)
            .where(Mark.examination_id == examination_id, Mark.student_id == student_id)
        )
        .all()
    )
    if not marks:
        raise HTTPException(status_code=404, detail="No marks found for this student/exam")

    results = [SubjectResult(subject=subj.name, score=float(mark.score)) for mark, subj in marks]
    rc = compute_report_card(student_id, results)

    row = ReportCard(
        student_id=student_id,
        examination_id=examination_id,
        average=rc.average,
        gpa=rc.gpa,
        overall_grade=rc.overall_grade,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="report_cards",
        resource_id=row.id,
        new_value={"average": rc.average, "grade": rc.overall_grade, "gpa": rc.gpa},
    )
    db.commit()
    return ok(
        {
            "id": row.id,
            "average": rc.average,
            "gpa": rc.gpa,
            "overall_grade": rc.overall_grade,
            "subjects": [{"subject": r.subject, "score": r.score} for r in rc.results],
        },
        message="Report card generated",
    )
