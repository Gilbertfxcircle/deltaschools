"""Seed a sample school with users, staff, students and fees (section 14).

Usage::

    python scripts/seed_demo_data.py

Creates (idempotently) a demo institution ``demo`` in the global schema, enables
a representative set of modules, and populates the tenant schema with a
director, a teacher, students and a fee structure. Intended for local/dev use.

Assumes migrations have run and (for PostgreSQL) the ``school_demo`` schema
exists. For SQLite local deployments the tables live in the single database.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
for _candidate in (os.path.join(_HERE, "..", "backend"), os.path.join(_HERE, "..")):
    if os.path.isdir(os.path.join(_candidate, "app")):
        sys.path.insert(0, os.path.abspath(_candidate))
        break

from sqlalchemy import select  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import global_session, tenant_session  # noqa: E402
from app.models.global_models import Institution, InstitutionModule  # noqa: E402
from app.models.school_models import (  # noqa: E402
    FeeStructure,
    Staff,
    Student,
    User,
)

DEMO_TENANT = "demo"
DEMO_MODULES = [
    "attendance",
    "billing",
    "payroll",
    "library",
    "hostel",
    "transport",
    "lms",
    "hr_management",
    "communication_hub",
    "document_management",
    "parent_portal",
    "teacher_portal",
    "ai_assistant",
]


def _seed_global() -> None:
    with global_session() as db:
        inst = db.execute(
            select(Institution).where(Institution.tenant_id == DEMO_TENANT)
        ).scalar_one_or_none()
        if inst is None:
            db.add(
                Institution(
                    tenant_id=DEMO_TENANT,
                    name="Delta Plax Demo Secondary School",
                    institution_type="Secondary",
                    country="Uganda",
                )
            )
            print(f"[OK] Created demo institution '{DEMO_TENANT}'")
        for key in DEMO_MODULES:
            exists = db.execute(
                select(InstitutionModule).where(
                    InstitutionModule.tenant_id == DEMO_TENANT,
                    InstitutionModule.module_key == key,
                )
            ).scalar_one_or_none()
            if exists is None:
                db.add(InstitutionModule(tenant_id=DEMO_TENANT, module_key=key, enabled=True))
        print(f"[OK] Enabled modules: {', '.join(DEMO_MODULES)}")


def _seed_tenant() -> None:
    with tenant_session(DEMO_TENANT) as db:
        if db.execute(select(User).limit(1)).scalar_one_or_none() is None:
            db.add_all(
                [
                    User(
                        full_name="Grace Director",
                        email="director@demo.deltaplax.com",
                        password_hash=hash_password("Director#2026"),
                        role="SCHOOL_DIRECTOR",
                    ),
                    User(
                        full_name="Tom Teacher",
                        email="teacher@demo.deltaplax.com",
                        password_hash=hash_password("Teacher#2026"),
                        role="TEACHER",
                    ),
                ]
            )
            print("[OK] Created director + teacher users")

        if db.execute(select(Staff).limit(1)).scalar_one_or_none() is None:
            db.add(Staff(staff_no="ST-001", full_name="Tom Teacher", designation="Teacher"))

        if db.execute(select(Student).limit(1)).scalar_one_or_none() is None:
            db.add_all(
                [
                    Student(admission_no="ADM-001", first_name="Amina", last_name="Okello",
                            gender="F"),
                    Student(admission_no="ADM-002", first_name="Brian", last_name="Mwangi",
                            gender="M"),
                    Student(admission_no="ADM-003", first_name="Carol", last_name="Achieng",
                            gender="F"),
                ]
            )
            print("[OK] Created 3 demo students")

        if db.execute(select(FeeStructure).limit(1)).scalar_one_or_none() is None:
            db.add(
                FeeStructure(
                    name="S1 Tuition - Term 1",
                    academic_year="2026",
                    amount=450000,
                    currency="UGX",
                )
            )
            print("[OK] Created demo fee structure")


def main() -> None:
    print(f"Seeding demo data at {datetime.now(timezone.utc).isoformat()} ...")
    _seed_global()
    _seed_tenant()
    print("[DONE] Demo data seeded.")


if __name__ == "__main__":
    main()
