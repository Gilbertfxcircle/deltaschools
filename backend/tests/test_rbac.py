"""RBAC policy tests, including the Super Admin "forbidden writes" law (4.3)."""

import unittest

from app.core import rbac
from app.core.rbac import (
    FORBIDDEN_SUPER_ADMIN_PERMISSIONS,
    SUPER_ADMIN_PERMISSIONS,
    RBACError,
    Role,
    assert_super_admin_grant_is_safe,
    default_permissions_for,
    has_permission,
    requires_mfa,
)


class TestPermissionMatching(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(has_permission({"students:read"}, "students:read"))

    def test_no_match(self):
        self.assertFalse(has_permission({"students:read"}, "students:write"))

    def test_resource_wildcard(self):
        self.assertTrue(has_permission({"students:*"}, "students:write"))
        self.assertFalse(has_permission({"students:*"}, "marks:write"))

    def test_global_wildcard(self):
        self.assertTrue(has_permission({"*"}, "anything:goes"))


class TestSuperAdminForbiddenWrites(unittest.TestCase):
    """The platform owner may manage the platform but never write school data."""

    def test_default_super_admin_set_is_safe(self):
        # Must not raise.
        assert_super_admin_grant_is_safe(SUPER_ADMIN_PERMISSIONS)

    def test_super_admin_lacks_protected_writes(self):
        perms = default_permissions_for(Role.DELTA_PLAX_SUPER_ADMIN)
        for forbidden in ("students:write", "marks:write", "payments:write", "payroll:write"):
            self.assertFalse(
                has_permission(perms, forbidden),
                f"Super admin must NOT have {forbidden}",
            )

    def test_super_admin_can_request_approval(self):
        perms = default_permissions_for(Role.DELTA_PLAX_SUPER_ADMIN)
        self.assertTrue(has_permission(perms, "approval_requests:submit"))

    def test_granting_forbidden_permission_raises(self):
        for forbidden in FORBIDDEN_SUPER_ADMIN_PERMISSIONS:
            with self.assertRaises(RBACError):
                assert_super_admin_grant_is_safe({forbidden})

    def test_wildcard_implying_protected_write_raises(self):
        with self.assertRaises(RBACError):
            assert_super_admin_grant_is_safe({"students:*"})
        with self.assertRaises(RBACError):
            assert_super_admin_grant_is_safe({"*"})


class TestRoleDefaults(unittest.TestCase):
    def test_director_has_full_school_control(self):
        self.assertTrue(has_permission(default_permissions_for(Role.SCHOOL_DIRECTOR), "anything:x"))

    def test_teacher_can_write_marks_and_attendance(self):
        perms = default_permissions_for(Role.TEACHER)
        self.assertTrue(has_permission(perms, "marks:write"))
        self.assertTrue(has_permission(perms, "attendance:write"))

    def test_teacher_cannot_manage_finance(self):
        perms = default_permissions_for(Role.TEACHER)
        self.assertFalse(has_permission(perms, "finance:write"))

    def test_mfa_required_for_levels_1_to_5(self):
        for role in (
            Role.DELTA_PLAX_SUPER_ADMIN,
            Role.SCHOOL_DIRECTOR,
            Role.DEPUTY_DIRECTOR,
            Role.BURSAR,
            Role.ACADEMIC_REGISTRAR,
        ):
            self.assertTrue(requires_mfa(role), f"{role.name} should require MFA")

    def test_mfa_not_forced_below_level_5(self):
        for role in (Role.TEACHER, Role.PARENT, Role.STUDENT):
            self.assertFalse(requires_mfa(role))

    def test_role_levels_ordered(self):
        self.assertLess(Role.DELTA_PLAX_SUPER_ADMIN, Role.SCHOOL_DIRECTOR)
        self.assertLess(Role.SCHOOL_DIRECTOR, Role.TEACHER)


if __name__ == "__main__":
    unittest.main()
