"""Finance/billing computation (billing & mobile_money modules).

Pure money logic using Decimal to avoid float drift. Invoices accrue payments;
balances and statuses are derived deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class InvoiceStatus(str, Enum):
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERPAID = "overpaid"


class FinanceError(ValueError):
    """Raised on invalid financial input."""


def _money(value: float | str | Decimal) -> Decimal:
    """Coerce to a 2-dp Decimal, rejecting negatives."""
    d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if d < 0:
        raise FinanceError(f"Monetary value cannot be negative: {value}")
    return d


def invoice_status(amount: float | Decimal, paid: float | Decimal) -> InvoiceStatus:
    """Derive an invoice status from its amount and total paid."""
    amt = _money(amount)
    pd = _money(paid)
    if pd == 0:
        return InvoiceStatus.UNPAID
    if pd < amt:
        return InvoiceStatus.PARTIAL
    if pd == amt:
        return InvoiceStatus.PAID
    return InvoiceStatus.OVERPAID


def balance(amount: float | Decimal, paid: float | Decimal) -> Decimal:
    """Outstanding balance (>= 0; overpayment yields 0 balance)."""
    amt = _money(amount)
    pd = _money(paid)
    bal = amt - pd
    return bal if bal > 0 else Decimal("0.00")


def apply_payment(
    amount: float | Decimal, paid_so_far: float | Decimal, payment: float | Decimal
) -> tuple[Decimal, InvoiceStatus]:
    """Apply a payment, returning the new (balance, status).

    Raises:
        FinanceError: If the payment is zero or negative.
    """
    pay = _money(payment)
    if pay <= 0:
        raise FinanceError("Payment must be positive")
    new_paid = _money(paid_so_far) + pay
    return balance(amount, new_paid), invoice_status(amount, new_paid)


@dataclass(frozen=True)
class StudentLedger:
    student_id: str
    total_billed: Decimal
    total_paid: Decimal
    outstanding: Decimal


def student_ledger(
    student_id: str, invoices: list[tuple[float | Decimal, float | Decimal]]
) -> StudentLedger:
    """Aggregate a student's invoices into a ledger.

    ``invoices`` is a list of (amount, paid) tuples.
    """
    total_billed = sum((_money(a) for a, _ in invoices), Decimal("0.00"))
    total_paid = sum((_money(p) for _, p in invoices), Decimal("0.00"))
    outstanding = sum((balance(a, p) for a, p in invoices), Decimal("0.00"))
    return StudentLedger(
        student_id=student_id,
        total_billed=total_billed,
        total_paid=total_paid,
        outstanding=outstanding,
    )
