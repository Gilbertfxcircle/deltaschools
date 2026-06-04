"""Immutable audit trail primitives - section 3.3 of the brief.

LAW #4: *The audit log is sacred.* No code path may modify or delete an audit
record. Immutability is enforced at three layers:

1. **Database** - a ``BEFORE UPDATE OR DELETE`` trigger raises (see the Alembic
   migration ``0001_initial_global_schema``).
2. **ORM** - audit models expose no update/delete paths in the repository layer.
3. **Domain object** - :class:`AuditRecord` is a frozen dataclass, so mutating
   an instance in Python raises ``FrozenInstanceError``.

This module is pure (stdlib only) so the envelope shape and immutability can be
unit-tested without a database.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum


class AuditAction(str, Enum):
    """Auditable actions."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    EXPORT = "EXPORT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"


class ApprovalStatus(str, Enum):
    """Approval state attached to an audited mutation."""

    AUTO = "auto"          # change applied immediately (not protected data)
    PENDING = "pending"    # awaiting director approval
    APPROVED = "approved"
    REJECTED = "rejected"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AuditRecord:
    """A single, immutable audit entry matching the brief's JSON contract.

    Being ``frozen`` means any attempt to reassign a field raises
    ``dataclasses.FrozenInstanceError`` - the in-memory guarantee that mirrors
    the database trigger.
    """

    user_id: str
    user_email: str
    role: str
    school_id: str
    action: AuditAction
    resource: str
    resource_id: str | None = None
    ip_address: str | None = None
    device_fingerprint: str | None = None
    previous_value: dict | None = None
    new_value: dict | None = None
    approval_status: ApprovalStatus = ApprovalStatus.AUTO
    approved_by: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        """Serialize to the exact envelope described in section 3.3."""
        data = asdict(self)
        data["action"] = self.action.value
        data["approval_status"] = self.approval_status.value
        return data


def build_audit_record(
    *,
    user_id: str,
    user_email: str,
    role: str,
    school_id: str,
    action: AuditAction,
    resource: str,
    resource_id: str | None = None,
    ip_address: str | None = None,
    device_fingerprint: str | None = None,
    previous_value: dict | None = None,
    new_value: dict | None = None,
    approval_status: ApprovalStatus = ApprovalStatus.AUTO,
    approved_by: str | None = None,
) -> AuditRecord:
    """Factory that stamps a new audit record with a fresh id and UTC timestamp."""
    return AuditRecord(
        user_id=user_id,
        user_email=user_email,
        role=role,
        school_id=school_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        ip_address=ip_address,
        device_fingerprint=device_fingerprint,
        previous_value=previous_value,
        new_value=new_value,
        approval_status=approval_status,
        approved_by=approved_by,
    )
