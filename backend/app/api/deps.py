"""Reusable FastAPI dependencies: current user, tenant session, RBAC guard.

All API routes pass through these guards (section 10: every route checks both
role and permission).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core import rbac
from app.core.security import decode_token
from app.db.session import SessionLocal, tenant_session

_bearer = HTTPBearer(auto_error=True)


@dataclass
class CurrentUser:
    """The authenticated principal extracted from a validated JWT."""

    id: str
    email: str
    role: str
    tenant: str | None
    permissions: frozenset[str]


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> CurrentUser:
    """Decode and validate the bearer token into a :class:`CurrentUser`."""
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}"
        ) from exc
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token"
        )
    return CurrentUser(
        id=payload["sub"],
        email=payload.get("email", ""),
        role=payload.get("role", ""),
        tenant=payload.get("tenant"),
        permissions=frozenset(payload.get("permissions", [])),
    )


def require_permission(permission: str):
    """Dependency factory enforcing a specific permission on a route."""

    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if not rbac.has_permission(user.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        return user

    return _guard


def require_super_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Allow only the Delta Plax platform super admin."""
    if user.role != rbac.Role.DELTA_PLAX_SUPER_ADMIN.name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Super admin only"
        )
    return user


def get_db() -> Iterator[Session]:
    """A plain (global) DB session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_tenant_db(request: Request) -> Iterator[Session]:
    """A tenant-scoped DB session bound to the schema resolved by middleware."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not identified")
    with tenant_session(tenant_id) as session:
        yield session
