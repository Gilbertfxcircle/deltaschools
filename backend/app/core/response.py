"""Consistent API response envelope - section 16 of the brief.

Every API response follows::

    { "success": true, "data": { ... }, "message": "OK", "errors": [] }

Pure helper (no third-party imports) so it can be reused and tested anywhere.
"""

from __future__ import annotations

from typing import Any


def envelope(
    *,
    success: bool = True,
    data: Any = None,
    message: str = "OK",
    errors: list[str] | None = None,
) -> dict[str, Any]:
    """Build the standard response envelope."""
    return {
        "success": success,
        "data": data,
        "message": message,
        "errors": errors or [],
    }


def ok(data: Any = None, message: str = "OK") -> dict[str, Any]:
    """Shortcut for a successful envelope."""
    return envelope(success=True, data=data, message=message)


def fail(message: str, errors: list[str] | None = None) -> dict[str, Any]:
    """Shortcut for a failure envelope."""
    return envelope(success=False, data=None, message=message, errors=errors)
