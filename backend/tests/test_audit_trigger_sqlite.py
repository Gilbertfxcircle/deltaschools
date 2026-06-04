"""DB-level proof of LAW #4 using stdlib sqlite3.

This installs the exact SQLite immutability triggers used by
``app.db.provisioning`` / migration 0001 and asserts that UPDATE and DELETE on an
audit row are rejected by the database itself, while INSERT still works. It uses
only the stdlib ``sqlite3`` module so it runs without third-party dependencies.

The PostgreSQL equivalent (PL/pgSQL ``RAISE EXCEPTION``) is exercised by the
integration suite against a live Postgres instance.
"""

import sqlite3
import unittest

AUDIT_MSG = "Audit logs are immutable and cannot be modified or deleted."

CREATE_TABLE = """
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT NOT NULL
);
"""

TRIGGER_NO_UPDATE = f"""
CREATE TRIGGER audit_log_no_update
BEFORE UPDATE ON audit_log
BEGIN
    SELECT RAISE(ABORT, '{AUDIT_MSG}');
END;
"""

TRIGGER_NO_DELETE = f"""
CREATE TRIGGER audit_log_no_delete
BEFORE DELETE ON audit_log
BEGIN
    SELECT RAISE(ABORT, '{AUDIT_MSG}');
END;
"""


class TestSqliteAuditImmutability(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        cur = self.conn.cursor()
        cur.executescript(CREATE_TABLE + TRIGGER_NO_UPDATE + TRIGGER_NO_DELETE)
        cur.execute(
            "INSERT INTO audit_log (id, timestamp, user_id, action, resource) "
            "VALUES ('a1', '2026-06-04T12:00:00Z', 'u1', 'CREATE', 'students')"
        )
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_insert_is_allowed(self):
        self.conn.execute(
            "INSERT INTO audit_log (id, timestamp, user_id, action, resource) "
            "VALUES ('a2', '2026-06-04T12:01:00Z', 'u1', 'LOGIN', 'auth')"
        )
        self.conn.commit()
        count = self.conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
        self.assertEqual(count, 2)

    def test_update_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError) as ctx:
            self.conn.execute("UPDATE audit_log SET action = 'DELETE' WHERE id = 'a1'")
        self.assertIn("immutable", str(ctx.exception).lower())

    def test_delete_is_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("DELETE FROM audit_log WHERE id = 'a1'")

    def test_row_unchanged_after_failed_update(self):
        try:
            self.conn.execute("UPDATE audit_log SET action = 'DELETE' WHERE id = 'a1'")
        except sqlite3.IntegrityError:
            pass
        action = self.conn.execute("SELECT action FROM audit_log WHERE id = 'a1'").fetchone()[0]
        self.assertEqual(action, "CREATE")


if __name__ == "__main__":
    unittest.main()
