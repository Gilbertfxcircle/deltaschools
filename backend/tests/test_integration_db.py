"""Integration tests against a real (SQLite) database.

These require the third-party stack. They are written so that, without
dependencies installed, ``python -m unittest`` simply SKIPS them (the heavy
imports live inside ``setUpClass``, and the class is guarded by
``skipUnless``). With ``pip install -r requirements.txt`` they run under both
``pytest`` and ``unittest`` and prove, end to end:

* tenant provisioning creates the per-school tables;
* a student round-trips through a tenant-scoped session;
* AES-256 field encryption round-trips;
* the audit-log immutability trigger rejects UPDATE/DELETE on a live DB.
"""

from __future__ import annotations

import os
import tempfile
import unittest

try:
    import sqlalchemy  # noqa: F401

    HAS_DEPS = True
except Exception:  # pragma: no cover - exercised only without deps
    HAS_DEPS = False


@unittest.skipUnless(HAS_DEPS, "requires SQLAlchemy + app dependencies")
class TestDatabaseIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        db_path = os.path.join(tempfile.gettempdir(), "deltaplax_itest.sqlite3")
        if os.path.exists(db_path):
            os.remove(db_path)
        # Env must be set before importing app modules that read settings.
        os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{db_path}"
        os.environ.setdefault("SECRET_KEY", "itest-secret-key")
        os.environ.setdefault("ENCRYPTION_KEY", "itest-encryption-key-0001")

        from sqlalchemy import select, text  # noqa: F401

        from app.db.provisioning import provision_tenant
        from app.db.session import tenant_session
        from app.models.school_models import SchoolAuditLog, Student

        cls.select = select
        cls.text = text
        cls.tenant_session = staticmethod(tenant_session)
        cls.Student = Student
        cls.SchoolAuditLog = SchoolAuditLog
        cls.db_path = db_path

        # Provision twice to prove idempotency.
        provision_tenant("demo")
        provision_tenant("demo")

    @classmethod
    def tearDownClass(cls) -> None:
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def test_student_round_trip(self):
        with self.tenant_session("demo") as db:
            db.add(self.Student(admission_no="ADM-IT-1", first_name="Ada", last_name="Lovelace"))
        with self.tenant_session("demo") as db:
            row = db.execute(
                self.select(self.Student).where(self.Student.admission_no == "ADM-IT-1")
            ).scalar_one()
            self.assertEqual(row.first_name, "Ada")

    def test_field_encryption_round_trip(self):
        from app.core.security import decrypt_field, encrypt_field

        token = encrypt_field("CM1234567")
        self.assertNotIn("CM1234567", token)
        self.assertEqual(decrypt_field(token), "CM1234567")

    def test_audit_insert_then_update_rejected(self):
        from datetime import datetime, timezone

        with self.tenant_session("demo") as db:
            db.add(
                self.SchoolAuditLog(
                    id="aud-it-1",
                    timestamp=datetime.now(timezone.utc),
                    user_id="u1",
                    user_email="x@demo",
                    role="BURSAR",
                    school_id="demo",
                    action="CREATE",
                    resource="students",
                )
            )
        # UPDATE must be rejected by the DB trigger.
        with self.assertRaises(Exception):
            with self.tenant_session("demo") as db:
                db.execute(self.text("UPDATE audit_log SET action='DELETE' WHERE id='aud-it-1'"))
        # DELETE must be rejected too.
        with self.assertRaises(Exception):
            with self.tenant_session("demo") as db:
                db.execute(self.text("DELETE FROM audit_log WHERE id='aud-it-1'"))
        # Row survives unchanged.
        with self.tenant_session("demo") as db:
            row = db.execute(
                self.select(self.SchoolAuditLog).where(self.SchoolAuditLog.id == "aud-it-1")
            ).scalar_one()
            self.assertEqual(row.action, "CREATE")


if __name__ == "__main__":
    unittest.main()
