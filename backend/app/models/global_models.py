"""Global (platform) schema models -> ``deltaplax_global`` (section 3.2)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GlobalBase
from app.models.mixins import TimestampMixin, UUIDPKMixin


class Institution(GlobalBase, UUIDPKMixin, TimestampMixin):
    """A registered school. ``tenant_id`` maps to its ``school_{id}`` schema."""

    __tablename__ = "institutions"

    tenant_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    institution_type: Mapped[str] = mapped_column(String(50))  # Primary/Secondary/...
    country: Mapped[str] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    branding_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class InstitutionModule(GlobalBase, UUIDPKMixin, TimestampMixin):
    """Which modules (feature flags) are enabled per institution (section 7)."""

    __tablename__ = "institution_modules"

    tenant_id: Mapped[str] = mapped_column(String(40), index=True)
    module_key: Mapped[str] = mapped_column(String(50))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class Subscription(GlobalBase, UUIDPKMixin, TimestampMixin):
    """Billing/licensing per school."""

    __tablename__ = "subscriptions"

    tenant_id: Mapped[str] = mapped_column(String(40), index=True)
    plan: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="active")
    seats: Mapped[int] = mapped_column(Integer, default=0)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SuperAdmin(GlobalBase, UUIDPKMixin, TimestampMixin):
    """Delta Plax internal staff. Created ONLY via the bootstrap script."""

    __tablename__ = "super_admins"

    full_name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="SUPER_ADMIN")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AuditLogGlobal(GlobalBase, UUIDPKMixin):
    """Platform-wide immutable audit trail.

    Immutability is enforced by a DB trigger created in the initial migration;
    no UPDATE/DELETE path exists in the application layer.
    """

    __tablename__ = "audit_log_global"

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_id: Mapped[str] = mapped_column(String(36))
    user_email: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50))
    school_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    action: Mapped[str] = mapped_column(String(20))
    resource: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    previous_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(20), default="auto")
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SyncManifest(GlobalBase, UUIDPKMixin, TimestampMixin):
    """Tracks cloud<->local sync state per institution (section 6)."""

    __tablename__ = "sync_manifest"

    tenant_id: Mapped[str] = mapped_column(String(40), index=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_cursor: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ApprovalRequestModel(GlobalBase, UUIDPKMixin, TimestampMixin):
    """Pending data-modification approvals (section 4.4).

    Drives the :class:`app.domain.approvals.ApprovalRequest` state machine.
    """

    __tablename__ = "approval_requests"

    tenant_id: Mapped[str] = mapped_column(String(40), index=True)
    resource: Mapped[str] = mapped_column(String(64))
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    requested_change: Mapped[str] = mapped_column(Text)  # JSON payload
    reason: Mapped[str] = mapped_column(Text)
    requested_by: Mapped[str] = mapped_column(String(36))
    state: Mapped[str] = mapped_column(String(20), default="pending")
    decided_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
