"""Approval workflow state machine - sections 4.4 & 6.3 of the brief.

When a Delta Plax Super Admin needs to modify protected school data, they may
only *request* the change. The change is applied **only** after the School
Director (or an authorized role) approves it. The same machine governs offline
sync-conflict resolution.

This is a pure state machine: no DB, no framework. Persistence and audit logging
are handled by the service layer that drives it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"  # approved AND the change has been committed to data


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


# Resources that are "protected": they can never be written directly by a super
# admin and always require an approval request to modify.
PROTECTED_RESOURCES: frozenset[str] = frozenset(
    {"students", "marks", "payments", "payroll", "report_cards", "invoices"}
)


class ApprovalError(RuntimeError):
    """Raised on an illegal approval-workflow transition."""


def requires_approval(resource: str) -> bool:
    """True if modifying ``resource`` must go through the approval workflow."""
    return resource in PROTECTED_RESOURCES


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ApprovalRequest:
    """An in-flight request to modify protected data.

    The state machine guarantees:
      * a request can be decided exactly once (no double-approve/reject);
      * a change is only ever ``APPLIED`` after an ``APPROVED`` decision;
      * a rejected request can never be applied.
    """

    school_id: str
    resource: str
    resource_id: str | None
    requested_change: dict
    requested_by: str
    reason: str
    state: ApprovalState = ApprovalState.PENDING
    decided_by: str | None = None
    decided_at: datetime | None = None
    decision_notes: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def decide(
        self,
        *,
        decision: ApprovalDecision,
        decided_by: str,
        notes: str | None = None,
        now: datetime | None = None,
    ) -> None:
        """Approve or reject a pending request.

        Raises:
            ApprovalError: If the request is not in the ``PENDING`` state.
        """
        if self.state != ApprovalState.PENDING:
            raise ApprovalError(
                f"Cannot decide a request already in state '{self.state.value}'"
            )
        self.state = (
            ApprovalState.APPROVED
            if decision == ApprovalDecision.APPROVED
            else ApprovalState.REJECTED
        )
        self.decided_by = decided_by
        self.decided_at = now or _utcnow()
        self.decision_notes = notes

    def mark_applied(self) -> None:
        """Transition an approved request to ``APPLIED`` once the change commits.

        Raises:
            ApprovalError: If the request was not approved first. This is the
                guard that makes it impossible to apply a rejected/pending change.
        """
        if self.state != ApprovalState.APPROVED:
            raise ApprovalError(
                "Change may only be applied after the request is APPROVED "
                f"(current state: '{self.state.value}')"
            )
        self.state = ApprovalState.APPLIED

    @property
    def is_actionable(self) -> bool:
        """True if an approved change is ready to be committed to data."""
        return self.state == ApprovalState.APPROVED
