"""Approval workflow state-machine tests (sections 4.4 & 6.3).

Proves: protected data needs approval; a request is decided once; a change is
only applied after approval; a rejected change can never be applied.
"""

import unittest

from app.domain.approvals import (
    ApprovalDecision,
    ApprovalError,
    ApprovalRequest,
    ApprovalState,
    requires_approval,
)


def _req(resource: str = "marks") -> ApprovalRequest:
    return ApprovalRequest(
        school_id="demo",
        resource=resource,
        resource_id="m1",
        requested_change={"score": 88},
        requested_by="superadmin-1",
        reason="Data correction requested by school",
    )


class TestProtectedResources(unittest.TestCase):
    def test_protected_resources_require_approval(self):
        for r in ("students", "marks", "payments", "payroll"):
            self.assertTrue(requires_approval(r))

    def test_non_protected_resource(self):
        self.assertFalse(requires_approval("library_books"))


class TestApprovalLifecycle(unittest.TestCase):
    def test_starts_pending(self):
        self.assertEqual(_req().state, ApprovalState.PENDING)

    def test_approve_then_apply(self):
        req = _req()
        req.decide(decision=ApprovalDecision.APPROVED, decided_by="director-1")
        self.assertEqual(req.state, ApprovalState.APPROVED)
        self.assertTrue(req.is_actionable)
        req.mark_applied()
        self.assertEqual(req.state, ApprovalState.APPLIED)

    def test_reject_blocks_apply(self):
        req = _req()
        req.decide(decision=ApprovalDecision.REJECTED, decided_by="director-1", notes="No")
        self.assertEqual(req.state, ApprovalState.REJECTED)
        self.assertFalse(req.is_actionable)
        with self.assertRaises(ApprovalError):
            req.mark_applied()

    def test_cannot_decide_twice(self):
        req = _req()
        req.decide(decision=ApprovalDecision.APPROVED, decided_by="d1")
        with self.assertRaises(ApprovalError):
            req.decide(decision=ApprovalDecision.REJECTED, decided_by="d2")

    def test_cannot_apply_pending(self):
        with self.assertRaises(ApprovalError):
            _req().mark_applied()

    def test_decision_metadata_recorded(self):
        req = _req()
        req.decide(decision=ApprovalDecision.APPROVED, decided_by="director-9", notes="ok")
        self.assertEqual(req.decided_by, "director-9")
        self.assertEqual(req.decision_notes, "ok")
        self.assertIsNotNone(req.decided_at)


if __name__ == "__main__":
    unittest.main()
