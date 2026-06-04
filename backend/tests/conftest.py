"""Pytest fixtures for integration tests.

These fixtures require the third-party stack (SQLAlchemy etc.). The pure
"laws" tests do not import this module's heavy dependencies, so they continue to
run under plain ``python -m unittest`` with no dependencies installed.
"""

from __future__ import annotations

import os
import tempfile

import pytest

# Use a throwaway SQLite file so provisioning + triggers run against a real DB.
_TMP_DB = os.path.join(tempfile.gettempdir(), "deltaplax_test.sqlite3")
os.environ.setdefault("DATABASE_URL", f"sqlite+pysqlite:///{_TMP_DB}")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use-only")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-not-for-production-0001")


@pytest.fixture(scope="session", autouse=True)
def _clean_db():
    """Remove any leftover test DB before and after the session."""
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)
    yield
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)
