"""Payroll computation tests."""

import unittest
from decimal import Decimal

from app.domain.payroll import PayrollError, compute_paye, compute_payslip


class TestPaye(unittest.TestCase):
    def test_zero_below_threshold(self):
        # Entirely within the 0% band.
        self.assertEqual(compute_paye(200000), Decimal("0.00"))

    def test_progressive_marginal(self):
        # 500000 gross crosses all bands; tax is positive and below flat 30%.
        tax = compute_paye(500000)
        self.assertGreater(tax, Decimal("0.00"))
        self.assertLess(tax, Decimal("150000.00"))  # < 30% of gross

    def test_negative_gross_rejected(self):
        with self.assertRaises(PayrollError):
            compute_paye(-1)


class TestPayslip(unittest.TestCase):
    def test_net_less_than_gross(self):
        slip = compute_payslip("s1", 500000)
        self.assertEqual(slip.gross, Decimal("500000.00"))
        self.assertLess(slip.net, slip.gross)
        # net = gross - paye - other
        self.assertEqual(slip.net, slip.gross - slip.paye - slip.other_deductions)

    def test_allowances_increase_base(self):
        base = compute_payslip("s1", 400000)
        with_allow = compute_payslip("s1", 400000, allowances=100000)
        self.assertEqual(with_allow.gross, Decimal("500000.00"))
        self.assertGreater(with_allow.gross, base.gross)

    def test_excessive_deductions_rejected(self):
        with self.assertRaises(PayrollError):
            compute_payslip("s1", 300000, other_deductions=400000)


if __name__ == "__main__":
    unittest.main()
