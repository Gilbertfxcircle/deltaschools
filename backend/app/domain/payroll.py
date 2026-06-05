"""Payroll computation (payroll & hr_management modules).

Pure logic: gross -> deductions (progressive tax bands + fixed deductions) ->
net. Tax bands are configurable; defaults are a simplified progressive scale.
This is illustrative computation, not tax/legal advice - each deployment
configures the statutory bands for its country.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


class PayrollError(ValueError):
    """Raised on invalid payroll input."""


def _money(value: float | str | Decimal) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Progressive monthly tax bands: (upper_bound_or_None, rate). Applied marginally.
DEFAULT_TAX_BANDS: tuple[tuple[Decimal | None, Decimal], ...] = (
    (Decimal("235000"), Decimal("0.0")),
    (Decimal("335000"), Decimal("0.10")),
    (Decimal("410000"), Decimal("0.20")),
    (None, Decimal("0.30")),
)


def compute_paye(
    gross: float | Decimal,
    bands: tuple[tuple[Decimal | None, Decimal], ...] = DEFAULT_TAX_BANDS,
) -> Decimal:
    """Compute progressive (marginal) tax on a gross amount."""
    g = _money(gross)
    if g < 0:
        raise PayrollError("Gross pay cannot be negative")
    tax = Decimal("0.00")
    lower = Decimal("0")
    for upper, rate in bands:
        taxable = (g - lower) if upper is None else (min(g, upper) - lower)
        if taxable > 0:
            tax += taxable * rate
        if upper is None or g <= upper:
            break
        lower = upper
    return _money(tax)


@dataclass(frozen=True)
class Payslip:
    staff_id: str
    gross: Decimal
    paye: Decimal
    other_deductions: Decimal
    net: Decimal


def compute_payslip(
    staff_id: str,
    gross: float | Decimal,
    allowances: float | Decimal = 0,
    other_deductions: float | Decimal = 0,
    bands: tuple[tuple[Decimal | None, Decimal], ...] = DEFAULT_TAX_BANDS,
) -> Payslip:
    """Compute a payslip: net = gross + allowances - PAYE - other deductions.

    Raises:
        PayrollError: If the result would be negative (deductions exceed pay).
    """
    base = _money(gross) + _money(allowances)
    paye = compute_paye(base, bands)
    other = _money(other_deductions)
    net = base - paye - other
    if net < 0:
        raise PayrollError("Net pay would be negative; check deductions")
    return Payslip(
        staff_id=staff_id,
        gross=base,
        paye=paye,
        other_deductions=other,
        net=_money(net),
    )
