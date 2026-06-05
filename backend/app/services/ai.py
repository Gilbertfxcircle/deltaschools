"""AI assistant service (ai_assistant module) with graceful degradation.

Section 12 of the brief: all AI features must degrade gracefully if the AI
service is unavailable - show a manual fallback, never crash. This service
checks for a configured provider; when none is set (or a call fails), it returns
a deterministic, rule-based fallback and flags ``ai_used=False`` so the caller
can present a manual path.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings


@dataclass(frozen=True)
class AiResult:
    text: str
    ai_used: bool


def is_ai_available() -> bool:
    """True if an AI provider is configured."""
    return bool(get_settings().openai_api_key)


def _fallback_report_comment(average: float, attendance_rate: float) -> str:
    if average >= 80:
        perf = "excellent academic performance"
    elif average >= 60:
        perf = "good progress with room to grow"
    elif average >= 50:
        perf = "a fair performance that needs steady improvement"
    else:
        perf = "performance that requires close support and intervention"
    att = "consistent attendance" if attendance_rate >= 0.9 else "attendance that should improve"
    return f"The student shows {perf} and {att}. Continued effort is encouraged."


def generate_report_comment(
    student_name: str, average: float, attendance_rate: float
) -> AiResult:
    """Generate a report-card comment, falling back to a rule-based template.

    When a provider is configured a real call would be made here; on any failure
    we still return the deterministic fallback so report generation never breaks.
    """
    fallback = f"{student_name}: " + _fallback_report_comment(average, attendance_rate)
    if not is_ai_available():
        return AiResult(text=fallback, ai_used=False)
    try:
        # A real provider call would go here; intentionally not wired to avoid a
        # hard dependency. Any exception falls through to the manual fallback.
        raise RuntimeError("provider call not implemented in this build")
    except Exception:
        return AiResult(text=fallback, ai_used=False)


def generate_fee_reminder(student_name: str, balance: float, currency: str) -> AiResult:
    """Generate a fee-reminder message (rule-based fallback always available)."""
    fallback = (
        f"Dear parent/guardian, this is a reminder that {student_name} has an "
        f"outstanding balance of {balance:.2f} {currency}. Kindly clear it at "
        f"your earliest convenience. Thank you."
    )
    return AiResult(text=fallback, ai_used=False)
