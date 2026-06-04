"""Module gating tests (section 7): disabled modules leave no trace in nav."""

import unittest

from app.core.modules import (
    AVAILABLE_MODULES,
    ModuleError,
    NavItem,
    is_enabled,
    is_valid_module,
    validate_modules,
    visible_nav,
)

NAV = [
    NavItem(key="dashboard", label="Dashboard", path="/", module=None),
    NavItem(key="attendance", label="Attendance", path="/attendance", module="attendance"),
    NavItem(key="library", label="Library", path="/library", module="library"),
    NavItem(key="hostel", label="Hostel", path="/hostel", module="hostel"),
]


class TestModuleRegistry(unittest.TestCase):
    def test_known_modules(self):
        self.assertTrue(is_valid_module("attendance"))
        self.assertTrue(is_valid_module("payroll"))

    def test_unknown_module(self):
        self.assertFalse(is_valid_module("teleportation"))

    def test_validate_modules_rejects_unknown(self):
        with self.assertRaises(ModuleError):
            validate_modules({"attendance", "not_a_module"})

    def test_validate_modules_accepts_known(self):
        self.assertEqual(validate_modules({"attendance", "library"}), {"attendance", "library"})

    def test_registry_has_expected_count(self):
        self.assertEqual(len(AVAILABLE_MODULES), 18)


class TestNavGating(unittest.TestCase):
    def test_disabled_modules_are_invisible(self):
        enabled = {"attendance"}
        visible = visible_nav(NAV, enabled)
        keys = {item.key for item in visible}
        self.assertIn("dashboard", keys)   # always-on
        self.assertIn("attendance", keys)  # enabled
        self.assertNotIn("library", keys)  # disabled -> absent, not greyed out
        self.assertNotIn("hostel", keys)

    def test_no_modules_enabled_keeps_only_core(self):
        visible = visible_nav(NAV, set())
        self.assertEqual({i.key for i in visible}, {"dashboard"})

    def test_is_enabled(self):
        self.assertTrue(is_enabled("library", {"library"}))
        self.assertFalse(is_enabled("library", {"attendance"}))


if __name__ == "__main__":
    unittest.main()
