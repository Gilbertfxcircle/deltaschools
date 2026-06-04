"""Module (feature-flag) system - section 7 of the brief.

A disabled module must be *invisible* to school users: no grayed-out links, no
"coming soon". The frontend asks the backend which modules are enabled and
renders navigation strictly from that list. This module provides the canonical
registry and the filtering helpers used on both sides.

No third-party imports.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Canonical registry of every module that can be enabled per institution.
AVAILABLE_MODULES: frozenset[str] = frozenset(
    {
        "attendance",
        "billing",
        "mobile_money",
        "sms",
        "payroll",
        "hostel",
        "library",
        "transport",
        "lms",
        "parent_portal",
        "student_portal",
        "teacher_portal",
        "mobile_apps",
        "ai_assistant",
        "communication_hub",
        "biometric_attendance",
        "hr_management",
        "document_management",
    }
)


class ModuleError(ValueError):
    """Raised when an unknown module key is referenced."""


@dataclass(frozen=True)
class NavItem:
    """A single navigation entry guarded by a module flag.

    ``module`` of ``None`` means the item is always visible (core navigation
    that does not depend on an optional module).
    """

    key: str
    label: str
    path: str
    module: str | None = None


def is_valid_module(name: str) -> bool:
    """True if ``name`` is a known module key."""
    return name in AVAILABLE_MODULES


def validate_modules(names: set[str] | frozenset[str] | list[str]) -> set[str]:
    """Return the set of names, raising if any is not a known module."""
    unknown = {n for n in names if n not in AVAILABLE_MODULES}
    if unknown:
        raise ModuleError(f"Unknown module(s): {sorted(unknown)}")
    return set(names)


def is_enabled(module: str, enabled_modules: set[str] | frozenset[str]) -> bool:
    """True if ``module`` is enabled for the institution."""
    return module in enabled_modules


def visible_nav(
    nav_items: list[NavItem], enabled_modules: set[str] | frozenset[str]
) -> list[NavItem]:
    """Filter navigation to only items whose module is enabled (or always-on).

    This is the function that guarantees a disabled module leaves *no trace* in
    the UI: gated items are dropped entirely, not disabled.
    """
    return [
        item
        for item in nav_items
        if item.module is None or item.module in enabled_modules
    ]
