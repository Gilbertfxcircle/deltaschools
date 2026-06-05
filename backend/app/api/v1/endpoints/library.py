"""Library catalog + loans (library module)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import LibraryBook, LibraryLoan
from app.services.audit import audit_actor_school

router = APIRouter()


class BookCreate(BaseModel):
    title: str
    author: str | None = None
    isbn: str | None = None
    total_copies: int = 1


class LoanCreate(BaseModel):
    book_id: str
    borrower_id: str
    days: int = 14


@router.get("/books")
def list_books(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("library:read")),
) -> dict:
    rows = db.execute(select(LibraryBook)).scalars().all()
    return ok(
        [
            {"id": r.id, "title": r.title, "author": r.author,
             "available": r.available_copies, "total": r.total_copies}
            for r in rows
        ]
    )


@router.post("/books")
def add_book(
    payload: BookCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("library:write")),
) -> dict:
    row = LibraryBook(
        title=payload.title, author=payload.author, isbn=payload.isbn,
        total_copies=payload.total_copies, available_copies=payload.total_copies,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="library_books",
        resource_id=row.id, new_value={"title": payload.title},
    )
    db.commit()
    return ok({"id": row.id}, message="Book added")


@router.post("/loans")
def loan_book(
    payload: LoanCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("library:write")),
) -> dict:
    book = db.get(LibraryBook, payload.book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.available_copies <= 0:
        raise HTTPException(status_code=409, detail="No copies available")
    now = datetime.now(timezone.utc)
    loan = LibraryLoan(
        book_id=payload.book_id,
        borrower_id=payload.borrower_id,
        borrowed_at=now,
        due_at=now + timedelta(days=payload.days),
    )
    book.available_copies -= 1
    db.add(loan)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="library_loans",
        resource_id=loan.id, new_value={"book_id": payload.book_id, "borrower": payload.borrower_id},
    )
    db.commit()
    return ok({"id": loan.id, "due_at": loan.due_at.isoformat()}, message="Book loaned")


@router.post("/loans/{loan_id}/return")
def return_book(
    loan_id: str,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("library:write")),
) -> dict:
    loan = db.get(LibraryLoan, loan_id)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.returned_at is not None:
        raise HTTPException(status_code=409, detail="Already returned")
    loan.returned_at = datetime.now(timezone.utc)
    book = db.get(LibraryBook, loan.book_id)
    if book is not None:
        book.available_copies += 1
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.UPDATE, resource="library_loans",
        resource_id=loan.id, new_value={"returned": True},
    )
    db.commit()
    return ok({"id": loan.id}, message="Book returned")
