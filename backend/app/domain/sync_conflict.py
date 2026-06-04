"""Pure conflict-detection logic for the offline sync engine (section 6.3).

Kept free of third-party imports so the "never silently overwrite" rule is
unit-testable in isolation. The I/O-bound engine in
:mod:`app.services.sync` imports these types and the :func:`detect_conflict`
rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class RemoteRecord:
    """A record as seen on the cloud side, used for conflict detection."""

    resource: str
    resource_id: str
    updated_at: datetime
    checksum: str
    payload: dict[str, Any]


@dataclass
class LocalRecord:
    """A queued local change, used for conflict detection."""

    resource: str
    resource_id: str
    updated_at: datetime
    checksum: str
    payload: dict[str, Any]


def detect_conflict(
    local: LocalRecord, remote: RemoteRecord, last_sync: datetime | None
) -> bool:
    """Return True if both sides changed the same record since ``last_sync``.

    Rules:
      * Different records never conflict.
      * Identical checksums mean identical data -> no conflict.
      * With no prior sync we cannot prove which side is authoritative, so a
        checksum mismatch is treated as a conflict.
      * Otherwise it is a conflict only when *both* sides changed after the last
        successful sync (concurrent divergent edits).
    """
    if local.resource_id != remote.resource_id or local.resource != remote.resource:
        return False
    if local.checksum == remote.checksum:
        return False
    if last_sync is None:
        return True
    return local.updated_at > last_sync and remote.updated_at > last_sync
