"""Engine + tenant-scoped session management.

LAW #1 enforcement at runtime: :func:`tenant_session` opens a session and
immediately pins it to the correct schema via a *validated* ``SET search_path``
statement (see :func:`app.core.tenant.search_path_sql`). Every per-school query
made through that session is confined to the tenant's schema.

For SQLite (offline EXE) there are no schemas, so the search_path step is a
no-op and isolation is achieved by separate database files / the single local
tenant.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.tenant import schema_for_tenant, search_path_sql

_settings = get_settings()

# ``future=True`` selects SQLAlchemy 2.0 semantics. For SQLite we relax the
# same-thread check because the local server touches the DB from a background
# sync thread.
_engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
if _settings.is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(_settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def global_session() -> Iterator[Session]:
    """A session for platform-wide (``deltaplax_global``) operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def tenant_session(tenant_id: str) -> Iterator[Session]:
    """A session pinned to a single tenant's schema.

    The schema name is produced and validated by :func:`schema_for_tenant`, so
    the ``SET search_path`` statement can never carry untrusted input.
    """
    schema = schema_for_tenant(tenant_id)
    session = SessionLocal()
    try:
        if not _settings.is_sqlite:
            session.execute(text(search_path_sql(schema)))
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
