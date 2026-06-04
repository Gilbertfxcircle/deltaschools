"""initial global schema + immutable audit trigger

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

Creates the ``deltaplax_global`` schema and its tables, then installs the audit
immutability guard (LAW #4). The guard is implemented for both PostgreSQL
(PL/pgSQL ``BEFORE UPDATE OR DELETE`` trigger) and SQLite (``RAISE(ABORT)``
triggers) so the offline EXE deployment is equally protected.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GLOBAL_SCHEMA = "deltaplax_global"

AUDIT_IMMUTABLE_MSG = "Audit logs are immutable and cannot be modified or deleted."


def _schema(is_sqlite: bool) -> str | None:
    return None if is_sqlite else GLOBAL_SCHEMA


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    schema = _schema(is_sqlite)

    if not is_sqlite:
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {GLOBAL_SCHEMA}")

    op.create_table(
        "institutions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("institution_type", sa.String(50), nullable=False),
        sa.Column("country", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("branding_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", name="uq_institutions_tenant_id"),
        schema=schema,
    )

    op.create_table(
        "institution_modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("module_key", sa.String(50), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=schema,
    )

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("plan", sa.String(50), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("seats", sa.Integer, nullable=False, server_default="0"),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=schema,
    )

    op.create_table(
        "super_admins",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="SUPER_ADMIN"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("mfa_enabled", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("mfa_secret", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_super_admins_email"),
        schema=schema,
    )

    op.create_table(
        "audit_log_global",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("school_id", sa.String(40), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("device_fingerprint", sa.String(128), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("resource", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("previous_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("approval_status", sa.String(20), nullable=False, server_default="auto"),
        sa.Column("approved_by", sa.String(36), nullable=True),
        schema=schema,
    )

    op.create_table(
        "sync_manifest",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_cursor", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=schema,
    )

    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(40), nullable=False),
        sa.Column("resource", sa.String(64), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=True),
        sa.Column("requested_change", sa.Text, nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("requested_by", sa.String(36), nullable=False),
        sa.Column("state", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("decided_by", sa.String(36), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema=schema,
    )

    op.create_index("ix_institution_modules_tenant_id", "institution_modules", ["tenant_id"],
                    schema=schema)
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"], schema=schema)
    op.create_index("ix_sync_manifest_tenant_id", "sync_manifest", ["tenant_id"], schema=schema)
    op.create_index("ix_approval_requests_tenant_id", "approval_requests", ["tenant_id"],
                    schema=schema)

    _install_audit_immutability(is_sqlite, schema)


def _install_audit_immutability(is_sqlite: bool, schema: str | None) -> None:
    """Install the BEFORE UPDATE/DELETE guard on the global audit table."""
    if is_sqlite:
        op.execute(
            f"""
            CREATE TRIGGER audit_log_global_no_update
            BEFORE UPDATE ON audit_log_global
            BEGIN
                SELECT RAISE(ABORT, '{AUDIT_IMMUTABLE_MSG}');
            END;
            """
        )
        op.execute(
            f"""
            CREATE TRIGGER audit_log_global_no_delete
            BEFORE DELETE ON audit_log_global
            BEGIN
                SELECT RAISE(ABORT, '{AUDIT_IMMUTABLE_MSG}');
            END;
            """
        )
        return

    table = f"{schema}.audit_log_global"
    op.execute(
        f"""
        CREATE OR REPLACE FUNCTION {schema}.prevent_audit_modification()
        RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION '{AUDIT_IMMUTABLE_MSG}';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        f"""
        CREATE TRIGGER audit_log_global_immutable
        BEFORE UPDATE OR DELETE ON {table}
        FOR EACH ROW EXECUTE FUNCTION {schema}.prevent_audit_modification();
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"
    schema = _schema(is_sqlite)

    if is_sqlite:
        op.execute("DROP TRIGGER IF EXISTS audit_log_global_no_update")
        op.execute("DROP TRIGGER IF EXISTS audit_log_global_no_delete")
    else:
        op.execute(f"DROP TRIGGER IF EXISTS audit_log_global_immutable ON {schema}.audit_log_global")
        op.execute(f"DROP FUNCTION IF EXISTS {schema}.prevent_audit_modification()")

    for name in (
        "approval_requests",
        "sync_manifest",
        "audit_log_global",
        "super_admins",
        "subscriptions",
        "institution_modules",
        "institutions",
    ):
        op.drop_table(name, schema=schema)

    if not is_sqlite:
        op.execute(f"DROP SCHEMA IF EXISTS {GLOBAL_SCHEMA} CASCADE")
