"""Auth policy tests: password strength + 5-failures -> 15-minute lockout."""

import unittest
from datetime import datetime, timedelta, timezone

from app.core.security_policy import (
    LoginThrottle,
    is_strong_password,
    validate_password_strength,
)

T0 = datetime(2026, 6, 4, 12, 0, 0, tzinfo=timezone.utc)


class TestPasswordStrength(unittest.TestCase):
    def test_strong_password_accepted(self):
        self.assertTrue(is_strong_password("Delta#Plax2026"))

    def test_too_short_rejected(self):
        self.assertIn("at least", " ".join(validate_password_strength("Ab#1")))

    def test_requires_symbol(self):
        problems = validate_password_strength("Abcdefgh123")
        self.assertTrue(any("symbol" in p for p in problems))

    def test_requires_upper_lower_digit(self):
        self.assertFalse(is_strong_password("alllowercase#1"))  # no uppercase
        self.assertFalse(is_strong_password("ALLUPPER#1"))      # no lowercase
        self.assertFalse(is_strong_password("NoDigits#Here"))   # no digit


class TestLoginThrottle(unittest.TestCase):
    def test_locks_after_five_failures(self):
        t = LoginThrottle(max_failed=5, lockout_minutes=15)
        for _ in range(4):
            self.assertFalse(t.register_failure(now=T0))
        self.assertFalse(t.is_locked(now=T0))
        # 5th failure triggers lockout.
        self.assertTrue(t.register_failure(now=T0))
        self.assertTrue(t.is_locked(now=T0))

    def test_lockout_expires_after_window(self):
        t = LoginThrottle(max_failed=5, lockout_minutes=15)
        for _ in range(5):
            t.register_failure(now=T0)
        self.assertTrue(t.is_locked(now=T0 + timedelta(minutes=14)))
        self.assertFalse(t.is_locked(now=T0 + timedelta(minutes=15)))

    def test_success_resets_counters(self):
        t = LoginThrottle()
        t.register_failure(now=T0)
        t.register_failure(now=T0)
        t.register_success()
        self.assertEqual(t.failed_count, 0)
        self.assertFalse(t.is_locked(now=T0))

    def test_retry_after_seconds(self):
        t = LoginThrottle(max_failed=1, lockout_minutes=15)
        t.register_failure(now=T0)
        self.assertEqual(t.retry_after_seconds(now=T0), 15 * 60)
        self.assertEqual(t.retry_after_seconds(now=T0 + timedelta(minutes=15)), 0)


if __name__ == "__main__":
    unittest.main()
