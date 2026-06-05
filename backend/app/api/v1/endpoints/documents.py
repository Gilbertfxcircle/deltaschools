"""Document management: file references in object storage (document_management).

This records document metadata (storage key, type, size). Actual binary upload
goes to MinIO/S3; uploads are validated for MIME-type consistency before being
recorded (section 10). The validation rule is pure and testable.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_tenant_db, require_permission
from app.core.audit import AuditAction
from app.core.response import ok
from app.models.school_models import Document
from app.services.audit import audit_actor_school
from app.services.storage import is_mime_consistent

router = APIRouter()


class DocumentRegister(BaseModel):
    name: str
    storage_key: str
    content_type: str
    size_bytes: int | None = None


@router.get("")
def list_documents(
    db: Session = Depends(get_tenant_db),
    _: CurrentUser = Depends(require_permission("documents:read")),
) -> dict:
    rows = db.execute(select(Document)).scalars().all()
    return ok(
        [{"id": r.id, "name": r.name, "content_type": r.content_type, "size": r.size_bytes}
         for r in rows]
    )


@router.post("")
def register_document(
    payload: DocumentRegister,
    db: Session = Depends(get_tenant_db),
    actor: CurrentUser = Depends(require_permission("documents:write")),
) -> dict:
    if not is_mime_consistent(payload.name, payload.content_type):
        raise HTTPException(
            status_code=400, detail="File extension does not match its declared content type"
        )
    row = Document(
        name=payload.name, storage_key=payload.storage_key,
        content_type=payload.content_type, size_bytes=payload.size_bytes, owner_id=actor.id,
    )
    db.add(row)
    db.flush()
    audit_actor_school(
        db, actor=actor, action=AuditAction.CREATE, resource="documents",
        resource_id=row.id, new_value={"name": payload.name, "type": payload.content_type},
    )
    db.commit()
    return ok({"id": row.id}, message="Document registered")
