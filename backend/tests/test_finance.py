"""Finance/billing computation tests."""

import unittest
from decimal import Decimal

from app.domain.finance import (
    FinanceError,
    InvoiceStatus,
    apply_payment,
    balance,
    invoice_status,
    student_ledger,
)


class TestInvoiceStatus(unittest.TestCase):
    def test_unpaid(self):
        self.assertEqual(invoice_status(100, 0), InvoiceStatus.UNPAID)

    def test_partial(self):
        self.assertEqual(invoice_status(100, 40), InvoiceStatus.PARTIAL)

    def test_paid_exact(self):
        self.assertEqual(invoice_status(100, 100), InvoiceStatus.PAID)

    def test_overpaid(self):
        self.assertEqual(invoice_status(100, 120), InvoiceStatus.OVERPAID)

    def test_negative_rejected(self):
        with self.assertRaises(FinanceError):
            invoice_status(-1, 0)


class TestBalanceAndPayment(unittest.TestCase):
    def test_balance(self):
        self.assertEqual(balance(100, 40), Decimal("60.00"))

    def test_balance_never_negative(self):
        self.assertEqual(balance(100, 150), Decimal("0.00"))

    def test_apply_payment(self):
        bal, status = apply_payment(100, 40, 60)
        self.assertEqual(bal, Decimal("0.00"))
        self.assertEqual(status, InvoiceStatus.PAID)

    def test_apply_zero_payment_rejected(self):
        with self.assertRaises(FinanceError):
            apply_payment(100, 0, 0)

    def test_decimal_precision(self):
        bal, _ = apply_payment("100.00", "33.33", "33.33")
        self.assertEqual(bal, Decimal("33.34"))


class TestStudentLedger(unittest.TestCase):
    def test_aggregates(self):
        ledger = student_ledger("stu1", [(100, 100), (200, 50), (50, 0)])
        self.assertEqual(ledger.total_billed, Decimal("350.00"))
        self.assertEqual(ledger.total_paid, Decimal("150.00"))
        self.assertEqual(ledger.outstanding, Decimal("200.00"))


if __name__ == "__main__":
    unittest.main()
