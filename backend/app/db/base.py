"""SQLAlchemy 2.0 declarative base and naming conventions.

Two metadata objects keep the two schema families separate at the ORM level:

* ``GlobalBase`` -> ``deltaplax_global`` (platform tables).
* ``SchoolBase`` -> per-tenant tables (no fixed schema; the schema is chosen at
  runtime via ``SET search_path`` so the same models serve every tenant).
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings
from app.core.tenant import GLOBAL_SCHEMA

# A consistent naming convention keeps Alembic autogenerate deterministic.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# SQLite has no notion of schemas, so the global tables live in the single
# database file there. On PostgreSQL they live in the dedicated global schema.
# Resolving this from settings is what lets the same models serve both the
# cloud (Postgres) and the offline EXE (SQLite) deployments.
_GLOBAL_SCHEMA = None if get_settings().is_sqlite else GLOBAL_SCHEMA


class GlobalBase(DeclarativeBase):
    """Base for tables that live in the global platform schema."""

    metadata = MetaData(
        naming_convention=NAMING_CONVENTION, schema=_GLOBAL_SCHEMA
    )


class SchoolBase(DeclarativeBase):
    """Base for per-tenant tables.

    No ``schema`` is bound here on purpose: the active schema is selected per
    request/session through ``SET search_path``, which is how one set of models
    serves every school while staying isolated.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
