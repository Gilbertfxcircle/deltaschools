"""Sync conflict-detection tests (section 6.3): never silently overwrite."""

import unittest
from datetime import datetime, timedelta, timezone

from app.domain.sync_conflict import LocalRecord, RemoteRecord, detect_conflict

T0 = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)


def _local(rid="s1", checksum="A", when=T0, resource="students"):
    return LocalRecord(resource=resource, resource_id=rid, updated_at=when,
                       checksum=checksum, payload={})


def _remote(rid="s1", checksum="B", when=T0, resource="students"):
    return RemoteRecord(resource=resource, resource_id=rid, updated_at=when,
                        checksum=checksum, payload={})


class TestConflictDetection(unittest.TestCase):
    def test_different_records_never_conflict(self):
        self.assertFalse(detect_conflict(_local(rid="s1"), _remote(rid="s2"), T0))
        self.assertFalse(
            detect_conflict(_local(resource="students"), _remote(resource="marks"), T0)
        )

    def test_identical_checksum_no_conflict(self):
        self.assertFalse(detect_conflict(_local(checksum="X"), _remote(checksum="X"), T0))

    def test_no_prior_sync_treats_mismatch_as_conflict(self):
        self.assertTrue(detect_conflict(_local(checksum="A"), _remote(checksum="B"), None))

    def test_concurrent_edits_conflict(self):
        last_sync = T0
        local = _local(checksum="A", when=last_sync + timedelta(minutes=5))
        remote = _remote(checksum="B", when=last_sync + timedelta(minutes=7))
        self.assertTrue(detect_conflict(local, remote, last_sync))

    def test_only_local_changed_no_conflict(self):
        last_sync = T0 + timedelta(minutes=10)
        local = _local(checksum="A", when=last_sync + timedelta(minutes=1))
        remote = _remote(checksum="B", when=T0)  # remote stale, unchanged since sync
        self.assertFalse(detect_conflict(local, remote, last_sync))

    def test_only_remote_changed_no_conflict(self):
        last_sync = T0 + timedelta(minutes=10)
        local = _local(checksum="A", when=T0)  # local stale
        remote = _remote(checksum="B", when=last_sync + timedelta(minutes=1))
        self.assertFalse(detect_conflict(local, remote, last_sync))


if __name__ == "__main__":
    unittest.main()
