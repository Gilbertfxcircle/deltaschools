"""AI assistant endpoints (ai_assistant module).

Every endpoint degrades gracefully: responses include ``ai_used`` so the client
can show that a manual/rule-based fallback was used when the AI provider is
unavailable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import CurrentUser, get_current_user
from app.core.response import ok
from app.services import ai

router = APIRouter()


class ReportCommentRequest(BaseModel):
    student_name: str
    average: float
    attendance_rate: float = 1.0


class FeeReminderRequest(BaseModel):
    student_name: str
    balance: float
    currency: str = "UGX"


@router.get("/status")
def ai_status(_: CurrentUser = Depends(get_current_user)) -> dict:
    """Report whether an AI provider is configured."""
    return ok({"available": ai.is_ai_available()})


@router.post("/report-comment")
def report_comment(
    payload: ReportCommentRequest,
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    result = ai.generate_report_comment(
        payload.student_name, payload.average, payload.attendance_rate
    )
    return ok({"comment": result.text, "ai_used": result.ai_used})


@router.post("/fee-reminder")
def fee_reminder(
    payload: FeeReminderRequest,
    _: CurrentUser = Depends(get_current_user),
) -> dict:
    result = ai.generate_fee_reminder(payload.student_name, payload.balance, payload.currency)
    return ok({"message": result.text, "ai_used": result.ai_used})
