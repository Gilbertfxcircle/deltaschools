"""Pure security policy: password strength + auth rate-limiting/lockout.

Section 10 of the brief: bcrypt hashing (cost >= 12), 5 failed logins -> 15-minute
lockout. The *policy* lives here as pure functions/state so it can be unit-tested
deterministically by injecting ``now``; the actual bcrypt/JWT work lives in
``app.core.security`` (which depends on third-party libraries).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

MIN_PASSWORD_LENGTH = 10
DEFAULT_MAX_FAILED = 5
DEFAULT_LOCKOUT_MINUTES = 15


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_password_strength(password: str) -> list[str]:
    """Return a list of human-readable problems; empty list means acceptable.

    Requires length >= 10 and a mix of lower, upper, digit and symbol.
    """
    problems: list[str] = []
    if len(password) < MIN_PASSWORD_LENGTH:
        problems.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters")
    if not any(c.islower() for c in password):
        problems.append("Password must contain a lowercase letter")
    if not any(c.isupper() for c in password):
        problems.append("Password must contain an uppercase letter")
    if not any(c.isdigit() for c in password):
        problems.append("Password must contain a digit")
    if all(c.isalnum() for c in password):
        problems.append("Password must contain a symbol")
    return problems


def is_strong_password(password: str) -> bool:
    """Convenience boolean wrapper around :func:`validate_password_strength`."""
    return not validate_password_strength(password)


@dataclass
class LoginThrottle:
    """Tracks failed-login attempts for a single principal (e.g. an email).

    Deterministic and side-effect free apart from its own counters, so tests can
    inject ``now`` to exercise the lockout window precisely.
    """

    max_failed: int = DEFAULT_MAX_FAILED
    lockout_minutes: int = DEFAULT_LOCKOUT_MINUTES
    failed_count: int = 0
    locked_until: datetime | None = field(default=None)

    def is_locked(self, now: datetime | None = None) -> bool:
        """True while the principal is inside an active lockout window."""
        now = now or _utcnow()
        if self.locked_until is None:
            return False
        if now >= self.locked_until:
            # Window elapsed: clear the lock and reset counters.
            self.locked_until = None
            self.failed_count = 0
            return False
        return True

    def register_failure(self, now: datetime | None = None) -> bool:
        """Record a failed attempt. Returns True if this triggered a lockout."""
        now = now or _utcnow()
        if self.is_locked(now):
            return True
        self.failed_count += 1
        if self.failed_count >= self.max_failed:
            self.locked_until = now + timedelta(minutes=self.lockout_minutes)
            return True
        return False

    def register_success(self) -> None:
        """Clear all counters after a successful authentication."""
        self.failed_count = 0
        self.locked_until = None

    def retry_after_seconds(self, now: datetime | None = None) -> int:
        """Seconds remaining until the lockout expires (0 if not locked)."""
        now = now or _utcnow()
        if self.locked_until is None or now >= self.locked_until:
            return 0
        return int((self.locked_until - now).total_seconds())
