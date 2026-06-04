"""Audit service - persists immutable audit records (section 16).

LAW: *Every database write must call the audit logger before returning a
response.* This service turns a pure :class:`app.core.audit.AuditRecord` into a
row in the school-level (``audit_log``) or platform-level (``audit_log_global``)
table. There is intentionally no update/delete here - records are write-once,
and the database trigger rejects any later modification (LAW #4).
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.core.audit import AuditAction, AuditRecord, ApprovalStatus, build_audit_record
from app.models.global_models import AuditLogGlobal
from app.models.school_models import SchoolAuditLog


def _dumps(value: dict | None) -> str | None:
    return None if value is None else json.dumps(value, default=str, sort_keys=True)


def record_school_audit(db: Session, audit: AuditRecord) -> SchoolAuditLog:
    """Persist an audit record into the current tenant's ``audit_log`` table.

    The session must already be pinned to the tenant schema (see
    :func:`app.db.session.tenant_session`).
    """
    row = SchoolAuditLog(
        id=audit.id,
        timestamp=_parse_ts(audit.timestamp),
        user_id=audit.user_id,
        user_email=audit.user_email,
        role=audit.role,
        school_id=audit.school_id,
        ip_address=audit.ip_address,
        device_fingerprint=audit.device_fingerprint,
        action=audit.action.value,
        resource=audit.resource,
        resource_id=audit.resource_id,
        previous_value=_dumps(audit.previous_value),
        new_value=_dumps(audit.new_value),
        approval_status=audit.approval_status.value,
        approved_by=audit.approved_by,
    )
    db.add(row)
    db.flush()  # surface DB errors (incl. immutability) before the response
    return row


def record_global_audit(db: Session, audit: AuditRecord) -> AuditLogGlobal:
    """Persist an audit record into the platform-wide ``audit_log_global`` table."""
    row = AuditLogGlobal(
        id=audit.id,
        timestamp=_parse_ts(audit.timestamp),
        user_id=audit.user_id,
        user_email=audit.user_email,
        role=audit.role,
        school_id=audit.school_id,
        ip_address=audit.ip_address,
        device_fingerprint=audit.device_fingerprint,
        action=audit.action.value,
        resource=audit.resource,
        resource_id=audit.resource_id,
        previous_value=_dumps(audit.previous_value),
        new_value=_dumps(audit.new_value),
        approval_status=audit.approval_status.value,
        approved_by=audit.approved_by,
    )
    db.add(row)
    db.flush()
    return row


def audit_actor_school(
    db: Session,
    *,
    actor: Any,
    action: AuditAction,
    resource: str,
    resource_id: str | None = None,
    previous_value: dict | None = None,
    new_value: dict | None = None,
    approval_status: ApprovalStatus = ApprovalStatus.AUTO,
    approved_by: str | None = None,
    ip_address: str | None = None,
    device_fingerprint: str | None = None,
) -> SchoolAuditLog:
    """Build + persist a school audit record from a ``CurrentUser``-like actor.

    ``actor`` must expose ``id``, ``email``, ``role`` and ``tenant``.
    """
    audit = _from_actor(
        actor, action, resource, resource_id, previous_value, new_value,
        approval_status, approved_by, ip_address, device_fingerprint,
    )
    return record_school_audit(db, audit)


def audit_actor_global(
    db: Session,
    *,
    actor: Any,
    action: AuditAction,
    resource: str,
    resource_id: str | None = None,
    previous_value: dict | None = None,
    new_value: dict | None = None,
    approval_status: ApprovalStatus = ApprovalStatus.AUTO,
    approved_by: str | None = None,
    ip_address: str | None = None,
    device_fingerprint: str | None = None,
) -> AuditLogGlobal:
    """Build + persist a platform (global) audit record from an actor."""
    audit = _from_actor(
        actor, action, resource, resource_id, previous_value, new_value,
        approval_status, approved_by, ip_address, device_fingerprint,
    )
    return record_global_audit(db, audit)


def _from_actor(
    actor: Any,
    action: AuditAction,
    resource: str,
    resource_id: str | None,
    previous_value: dict | None,
    new_value: dict | None,
    approval_status: ApprovalStatus,
    approved_by: str | None,
    ip_address: str | None,
    device_fingerprint: str | None,
) -> AuditRecord:
    return build_audit_record(
        user_id=getattr(actor, "id", "system"),
        user_email=getattr(actor, "email", ""),
        role=getattr(actor, "role", ""),
        school_id=getattr(actor, "tenant", "") or "",
        action=action,
        resource=resource,
        resource_id=resource_id,
        previous_value=previous_value,
        new_value=new_value,
        approval_status=approval_status,
        approved_by=approved_by,
        ip_address=ip_address,
        device_fingerprint=device_fingerprint,
    )


def _parse_ts(ts: str):
    from datetime import datetime

    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime.utcnow()
