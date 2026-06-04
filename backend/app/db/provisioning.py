"""Tenant (school) schema provisioning.

Called when a new institution is created (cloud) and on first run of the local
EXE. Creates the ``school_{id}`` schema, all per-school tables, and installs the
school-level audit immutability trigger (LAW #4) - the per-tenant counterpart of
the global trigger in migration ``0001``.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.db.base import SchoolBase
from app.db.session import engine as default_engine
from app.core.tenant import schema_for_tenant

_AUDIT_MSG = "Audit logs are immutable and cannot be modified or deleted."


def provision_tenant(tenant_id: str, engine: Engine | None = None) -> str:
    """Create the schema + tables + audit guard for a tenant. Returns the schema.

    Idempotent for table creation (``checkfirst=True``). Safe to call once per
    new school.
    """
    engine = engine or default_engine
    schema = schema_for_tenant(tenant_id)
    is_sqlite = engine.dialect.name == "sqlite"

    if not is_sqlite:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))

    # Create all per-school tables. On PostgreSQL we translate the unbound
    # SchoolBase metadata into the target schema; on SQLite they live in the
    # single local database.
    if is_sqlite:
        SchoolBase.metadata.create_all(bind=engine, checkfirst=True)
    else:
        with engine.connect() as conn:
            conn = conn.execution_options(schema_translate_map={None: schema})
            SchoolBase.metadata.create_all(bind=conn, checkfirst=True)
            conn.commit()

    _install_school_audit_trigger(engine, schema, is_sqlite)
    return schema


def _install_school_audit_trigger(engine: Engine, schema: str, is_sqlite: bool) -> None:
    with engine.begin() as conn:
        if is_sqlite:
            conn.execute(
                text(
                    f"CREATE TRIGGER IF NOT EXISTS {schema}_audit_no_update "
                    "BEFORE UPDATE ON audit_log "
                    f"BEGIN SELECT RAISE(ABORT, '{_AUDIT_MSG}'); END;"
                )
            )
            conn.execute(
                text(
                    f"CREATE TRIGGER IF NOT EXISTS {schema}_audit_no_delete "
                    "BEFORE DELETE ON audit_log "
                    f"BEGIN SELECT RAISE(ABORT, '{_AUDIT_MSG}'); END;"
                )
            )
        else:
            conn.execute(
                text(
                    f"CREATE OR REPLACE FUNCTION {schema}.prevent_audit_modification() "
                    "RETURNS trigger AS $$ BEGIN "
                    f"RAISE EXCEPTION '{_AUDIT_MSG}'; "
                    "END; $$ LANGUAGE plpgsql;"
                )
            )
            conn.execute(text(f"DROP TRIGGER IF EXISTS audit_log_immutable ON {schema}.audit_log"))
            conn.execute(
                text(
                    f"CREATE TRIGGER audit_log_immutable "
                    f"BEFORE UPDATE OR DELETE ON {schema}.audit_log "
                    f"FOR EACH ROW EXECUTE FUNCTION {schema}.prevent_audit_modification();"
                )
            )
