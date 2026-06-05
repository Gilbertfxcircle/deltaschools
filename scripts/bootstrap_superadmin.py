"""Delta Plax Super Admin Bootstrap Script (section 4.1).

Run ONCE during initial server deployment::

    python scripts/bootstrap_superadmin.py

LAW #2: the Super Admin account is *pre-created*, never registered. There is no
public registration endpoint for super admins. This script is idempotent - if
the account already exists it is left untouched.

The password is read from ``DELTAPLAX_ADMIN_PASSWORD`` and is required; it is
never hardcoded. The password is validated against the strength policy and
hashed with bcrypt (cost factor from settings, >= 12).
"""

from __future__ import annotations

import os
import sys
import uuid

# Make ``app`` importable whether running from the dev layout (repo/backend/app)
# or the container layout (/app/app, with scripts at /app/scripts).
_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in (os.path.join(_HERE, "..", "backend"), os.path.join(_HERE, "..")):
    if os.path.isdir(os.path.join(_candidate, "app")):
        sys.path.insert(0, os.path.abspath(_candidate))
        break

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.core.security_policy import validate_password_strength  # noqa: E402
from app.db.session import global_session  # noqa: E402
from app.models.global_models import SuperAdmin  # noqa: E402

SUPER_ADMIN_EMAIL = os.environ.get("DELTAPLAX_ADMIN_EMAIL", "admin@deltaplax.com")
SUPER_ADMIN_PASSWORD = os.environ.get("DELTAPLAX_ADMIN_PASSWORD")  # REQUIRED
SUPER_ADMIN_NAME = "Delta Plax Super Admin"


def bootstrap() -> None:
    if not SUPER_ADMIN_PASSWORD:
        raise EnvironmentError("DELTAPLAX_ADMIN_PASSWORD env variable is required.")

    problems = validate_password_strength(SUPER_ADMIN_PASSWORD)
    if problems:
        raise EnvironmentError("Weak DELTAPLAX_ADMIN_PASSWORD: " + "; ".join(problems))

    hashed = hash_password(SUPER_ADMIN_PASSWORD)

    # Using the ORM keeps this portable across PostgreSQL (global schema) and
    # SQLite (single file, no schemas) - the model carries the right schema.
    with global_session() as db:
        existing = db.execute(
            select(SuperAdmin).where(SuperAdmin.email == SUPER_ADMIN_EMAIL)
        ).scalar_one_or_none()

        if existing:
            print(f"[SKIP] Super admin '{SUPER_ADMIN_EMAIL}' already exists.")
            return

        db.add(
            SuperAdmin(
                id=str(uuid.uuid4()),
                full_name=SUPER_ADMIN_NAME,
                email=SUPER_ADMIN_EMAIL,
                password_hash=hashed,
                role="SUPER_ADMIN",
                is_active=True,
                mfa_enabled=False,
            )
        )
        print(f"[OK] Delta Plax Super Admin created: {SUPER_ADMIN_EMAIL}")


if __name__ == "__main__":
    bootstrap()
