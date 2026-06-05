"""Object storage helpers (MinIO/S3) + pure file-validation rules.

Section 10: all file uploads are scanned for MIME-type mismatch before storage.
The mismatch rule is pure and unit-tested here; the actual MinIO client wiring
is kept thin so the validation can be exercised without network/storage.
"""

from __future__ import annotations

import os

# Map common file extensions to their expected MIME type(s).
_EXTENSION_MIME: dict[str, frozenset[str]] = {
    ".pdf": frozenset({"application/pdf"}),
    ".png": frozenset({"image/png"}),
    ".jpg": frozenset({"image/jpeg"}),
    ".jpeg": frozenset({"image/jpeg"}),
    ".gif": frozenset({"image/gif"}),
    ".csv": frozenset({"text/csv", "application/csv"}),
    ".txt": frozenset({"text/plain"}),
    ".doc": frozenset({"application/msword"}),
    ".docx": frozenset(
        {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    ),
    ".xls": frozenset({"application/vnd.ms-excel"}),
    ".xlsx": frozenset(
        {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    ),
}


def is_mime_consistent(filename: str, content_type: str) -> bool:
    """True if a filename's extension matches its declared content type.

    Unknown extensions are allowed (returns True) since we cannot assert a
    mismatch; known extensions must match their expected MIME type.
    """
    _, ext = os.path.splitext(filename.lower())
    expected = _EXTENSION_MIME.get(ext)
    if expected is None:
        return True
    return content_type.lower() in expected
