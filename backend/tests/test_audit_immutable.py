"""LAW #4: audit records are immutable.

This covers the in-memory guarantee: an :class:`AuditRecord` is a frozen
dataclass, so any attempt to mutate it raises. The database-level guarantee (the
trigger that rejects UPDATE/DELETE) is verified by the integration test
``test_audit_trigger`` against a live DB; the SQLite variant of that trigger is
installed by ``app.db.provisioning`` and migration 0001.
"""

import dataclasses
import unittest

from app.core.audit import (
    ApprovalStatus,
    AuditAction,
    AuditRecord,
    build_audit_record,
)


def _record(**overrides) -> AuditRecord:
    base = dict(
        user_id="u1",
        user_email="bursar@demo.deltaplax.com",
        role="BURSAR",
        school_id="demo",
        action=AuditAction.UPDATE,
        resource="payments",
        resource_id="p1",
    )
    base.update(overrides)
    return build_audit_record(**base)


class TestAuditImmutability(unittest.TestCase):
    def test_cannot_mutate_existing_field(self):
        rec = _record()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rec.action = AuditAction.DELETE  # type: ignore[misc]

    def test_cannot_mutate_resource(self):
        rec = _record()
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rec.resource = "students"  # type: ignore[misc]

    def test_cannot_delete_field(self):
        rec = _record()
        with self.assertRaises((dataclasses.FrozenInstanceError, AttributeError)):
            del rec.user_id  # type: ignore[misc]


class TestAuditEnvelope(unittest.TestCase):
    def test_factory_stamps_id_and_timestamp(self):
        rec = _record()
        self.assertTrue(rec.id)
        self.assertTrue(rec.timestamp)
        # Two records get distinct ids.
        self.assertNotEqual(_record().id, _record().id)

    def test_to_dict_matches_contract(self):
        rec = _record(
            previous_value={"amount": 100},
            new_value={"amount": 120},
            approval_status=ApprovalStatus.APPROVED,
            approved_by="director-1",
        )
        d = rec.to_dict()
        expected_keys = {
            "id", "timestamp", "user_id", "user_email", "role", "school_id",
            "ip_address", "device_fingerprint", "action", "resource", "resource_id",
            "previous_value", "new_value", "approval_status", "approved_by",
        }
        self.assertEqual(set(d.keys()), expected_keys)
        self.assertEqual(d["action"], "UPDATE")
        self.assertEqual(d["approval_status"], "approved")
        self.assertEqual(d["previous_value"], {"amount": 100})


if __name__ == "__main__":
    unittest.main()
