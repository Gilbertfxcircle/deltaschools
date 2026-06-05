"""Finance: fee structures, invoices, payments (billing module).

Invoices and payments are protected financial data. Balances/statuses are
derived with the pure finance logic to avoid float drift.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.domain.finance import apply_payment, invoice_status
from app.models.school_models import FeeStructure, Invoice, Payment
from app.services.audit import audit_actor_school

router = APIRouter()


class FeeCreate(BaseModel):
    name: str
    academic_year: str
    amount: float
    currency: str = "UGX"


class InvoiceCreate(BaseModel):
    student_id: str
    fee_structure_id: str
    amount: float


class PaymentCreate(BaseModel):
    invoice_id: str
    student_id: str
    amount: float
    method: str = "cash"
    reference: str | None = None


@router.post("/fees")
def create_fee(
    payload: FeeCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("finance:write")),
) -> dict:
    row = FeeStructure(
        name=payload.name, academic_year=payload.academic_year,
        amount=payload.amount, currency=payload.currency,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="fee_structures",
        resource_id=row.id, new_value=payload.model_dump(),
    )
    db.commit()
    return ok({"id": row.id}, message="Fee structure created")


@router.post("/invoices")
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("finance:write")),
) -> dict:
    row = Invoice(
        student_id=payload.student_id,
        fee_structure_id=payload.fee_structure_id,
        amount=payload.amount,
        balance=payload.amount,
        status=invoice_status(payload.amount, 0).value,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="invoices",
        resource_id=row.id, new_value={"amount": payload.amount, "student_id": payload.student_id},
    )
    db.commit()
    return ok({"id": row.id, "balance": float(row.balance)}, message="Invoice created")


@router.post("/payments")
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("finance:write")),
) -> dict:
    invoice = db.get(Invoice, payload.invoice_id)
    if invoice is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    paid_so_far = float(invoice.amount) - float(invoice.balance)
    new_balance, status = apply_payment(float(invoice.amount), paid_so_far, payload.amount)

    payment = Payment(
        invoice_id=payload.invoice_id,
        student_id=payload.student_id,
        amount=payload.amount,
        method=payload.method,
        reference=payload.reference,
        paid_at=datetime.now(timezone.utc),
    )
    db.add(payment)
    previous = {"balance": float(invoice.balance), "status": invoice.status}
    invoice.balance = float(new_balance)
    invoice.status = status.value
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="payments",
        resource_id=payment.id,
        previous_value=previous,
        new_value={"amount": payload.amount, "balance": float(new_balance), "status": status.value},
    )
    db.commit()
    return ok(
        {"payment_id": payment.id, "balance": float(new_balance), "status": status.value},
        message="Payment recorded",
    )


@router.get("/invoices/student/{student_id}")
def student_invoices(
    student_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("finance:read")),
) -> dict:
    rows = db.execute(select(Invoice).where(Invoice.student_id == student_id)).scalars().all()
    return ok(
        [
            {"id": r.id, "amount": float(r.amount), "balance": float(r.balance), "status": r.status}
            for r in rows
        ]
    )
