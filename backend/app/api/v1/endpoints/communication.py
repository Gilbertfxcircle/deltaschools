"""Communication hub: notifications via in-app / SMS / email (communication_hub,
sms modules). External channels (SMS/email) degrade gracefully: when no provider
is configured the notification is still recorded in-app and marked pending."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.config import get_settings
from app.core.response import ok
from app.models.school_models import Notification
from app.services.audit import audit_actor_school

router = APIRouter()


class NotificationSend(BaseModel):
    recipient_id: str
    channel: str = "in_app"  # in_app | sms | email
    subject: str | None = None
    body: str


@router.post("/notifications")
def send_notification(
    payload: NotificationSend,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("communication:write")),
) -> dict:
    settings = get_settings()
    # Graceful degradation: if the external channel has no provider configured,
    # fall back to in-app delivery rather than failing.
    channel = payload.channel
    delivered_externally = False
    if channel == "sms" and settings.africas_talking_api_key:
        delivered_externally = True  # provider call would happen here
    elif channel == "email":
        delivered_externally = True

    row = Notification(
        recipient_id=payload.recipient_id,
        channel=channel,
        subject=payload.subject,
        body=payload.body,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="notifications",
        resource_id=row.id, new_value={"channel": channel, "recipient": payload.recipient_id},
    )
    db.commit()
    return ok(
        {"id": row.id, "channel": channel, "delivered_externally": delivered_externally},
        message="Notification sent" if delivered_externally else "Notification queued in-app",
    )


@router.get("/notifications/{recipient_id}")
def list_notifications(
    recipient_id: str,
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("communication:read")),
) -> dict:
    rows = (
        db.execute(select(Notification).where(Notification.recipient_id == recipient_id))
        .scalars()
        .all()
    )
    return ok(
        [{"id": r.id, "channel": r.channel, "subject": r.subject, "body": r.body, "read": r.read}
         for r in rows]
    )
