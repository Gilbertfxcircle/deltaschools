"""Role-Based Access Control primitives.

Encodes the user hierarchy and permission matrix from sections 4-5 of the brief.
No third-party imports: pure, testable policy.

Two laws are enforced here:

* **Least privilege for the platform owner.** The Delta Plax Super Admin can
  manage institutions, modules and subscriptions, but is *forbidden* from
  writing student records, marks, payments or payroll. To change protected
  school data the super admin must go through the approval workflow.
* **Per-institution configurability.** Default permission sets are seeded on
  school creation but can be overridden per institution.
"""

from __future__ import annotations

from enum import IntEnum


class Role(IntEnum):
    """User hierarchy. Lower number == higher privilege (Level 1 is highest)."""

    DELTA_PLAX_SUPER_ADMIN = 1
    SCHOOL_DIRECTOR = 2
    DEPUTY_DIRECTOR = 3
    BURSAR = 4
    ACADEMIC_REGISTRAR = 5
    DEPARTMENT_HEAD = 6
    TEACHER = 7
    PARENT = 8
    STUDENT = 9


#: Roles for which Two-Factor Authentication must be available (Levels 1-5).
MFA_REQUIRED_ROLES = frozenset(
    {
        Role.DELTA_PLAX_SUPER_ADMIN,
        Role.SCHOOL_DIRECTOR,
        Role.DEPUTY_DIRECTOR,
        Role.BURSAR,
        Role.ACADEMIC_REGISTRAR,
    }
)

# Wildcard permission that grants everything (use sparingly; never to super admin).
WILDCARD = "*"

# Permissions the platform Super Admin is explicitly ALLOWED to hold (section 4.3).
SUPER_ADMIN_PERMISSIONS: frozenset[str] = frozenset(
    {
        "institutions:create",
        "institutions:read",
        "institutions:activate",
        "institutions:suspend",
        "institutions:delete",
        "modules:enable",
        "modules:disable",
        "subscriptions:manage",
        "platform:analytics",
        "platform:health",
        "platform:audit_read",
        "users:create_school_admin",
        "approval_requests:submit",  # Can REQUEST edits to protected data only.
    }
)

# Writing protected school data is FORBIDDEN for the super admin, full stop.
# Any attempt to grant these to a super admin must raise.
FORBIDDEN_SUPER_ADMIN_PERMISSIONS: frozenset[str] = frozenset(
    {
        "students:write",
        "students:delete",
        "marks:write",
        "marks:delete",
        "payments:write",
        "payments:delete",
        "payroll:write",
        "payroll:delete",
    }
)


class RBACError(PermissionError):
    """Raised when a permission grant violates policy."""


def _matches(granted: str, required: str) -> bool:
    """Match a single granted permission against a required one, with wildcards.

    ``*`` matches anything; ``resource:*`` matches any action on a resource.
    """
    if granted == WILDCARD or granted == required:
        return True
    if granted.endswith(":*"):
        return required.startswith(granted[:-1])  # keep the trailing ':'
    return False


def has_permission(granted: set[str] | frozenset[str], required: str) -> bool:
    """True if any of the ``granted`` permissions satisfies ``required``."""
    return any(_matches(g, required) for g in granted)


def assert_super_admin_grant_is_safe(permissions: set[str] | frozenset[str]) -> None:
    """Guard: a Super Admin permission set must never include protected writes.

    Raises:
        RBACError: If a forbidden permission (or a wildcard that would imply one)
            is present.
    """
    if WILDCARD in permissions:
        raise RBACError("Super Admin must never be granted the '*' wildcard permission")
    for perm in permissions:
        if perm in FORBIDDEN_SUPER_ADMIN_PERMISSIONS:
            raise RBACError(f"Super Admin may not hold forbidden permission: {perm}")
        # A resource-wildcard like 'students:*' would imply 'students:write'.
        if perm.endswith(":*"):
            resource = perm[:-2]
            if any(f.startswith(resource + ":") for f in FORBIDDEN_SUPER_ADMIN_PERMISSIONS):
                raise RBACError(
                    f"Super Admin may not hold wildcard '{perm}' implying protected writes"
                )


# Default permission sets seeded into ``school_{id}.permissions`` on creation.
# These are starting points; each institution can customize them afterwards.
DEFAULT_ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    Role.SCHOOL_DIRECTOR: frozenset({WILDCARD}),  # full control inside the school
    Role.DEPUTY_DIRECTOR: frozenset(
        {
            "students:*",
            "staff:read",
            "staff:write",
            "academic:*",
            "attendance:*",
            "exams:*",
            "reports:*",
            "finance:read",
            "library:*",
            "hostel:*",
            "transport:*",
            "lms:*",
            "communication:*",
            "documents:*",
            "approvals:decide",
            "audit:read",
        }
    ),
    Role.BURSAR: frozenset(
        {
            "finance:*",
            "payroll:*",
            "students:read",
            "reports:read",
            "documents:read",
            "documents:write",
            "communication:write",
            "audit:read",
        }
    ),
    Role.ACADEMIC_REGISTRAR: frozenset(
        {
            "students:*",
            "enrollments:*",
            "academic:*",
            "exams:*",
            "marks:read",
            "attendance:read",
            "reports:*",
            "library:read",
            "lms:*",
            "communication:*",
            "documents:*",
            "approvals:decide",
        }
    ),
    Role.DEPARTMENT_HEAD: frozenset(
        {
            "academic:read",
            "marks:*",
            "exams:read",
            "exams:write",
            "attendance:*",
            "students:read",
            "reports:read",
            "lms:*",
            "library:read",
            "communication:write",
        }
    ),
    Role.TEACHER: frozenset(
        {
            "attendance:write",
            "attendance:read",
            "marks:write",
            "marks:read",
            "students:read",
            "academic:read",
            "lms:read",
            "lms:write",
            "library:read",
            "communication:write",
        }
    ),
    Role.PARENT: frozenset(
        {
            "students:read_own",
            "finance:read_own",
            "attendance:read_own",
            "reports:read_own",
            "communication:read",
        }
    ),
    Role.STUDENT: frozenset(
        {
            "students:read_self",
            "marks:read_self",
            "attendance:read_self",
            "lms:read",
            "library:read",
            "communication:read",
        }
    ),
}


def default_permissions_for(role: Role) -> frozenset[str]:
    """Return the seed permission set for a role (empty for unknown roles)."""
    if role == Role.DELTA_PLAX_SUPER_ADMIN:
        return SUPER_ADMIN_PERMISSIONS
    return DEFAULT_ROLE_PERMISSIONS.get(role, frozenset())


def requires_mfa(role: Role) -> bool:
    """True if the role is in the MFA-required band (Levels 1-5)."""
    return role in MFA_REQUIRED_ROLES
