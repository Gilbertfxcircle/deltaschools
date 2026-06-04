"""Authentication endpoints (section 9 ``/auth``, section 10 security).

Demonstrates the login flow with the pure lockout policy, JWT issuance and the
response envelope. Persistence/lookups are intentionally thin here; the focus of
this foundation is the security-critical control flow.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_tenant_db
from app.core import rbac
from app.core.response import ok
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    device_fingerprint,
    verify_password,
    verify_totp,
)
from app.core.security_policy import LoginThrottle
from app.models.school_models import User

router = APIRouter()

# In-memory throttle store. In production this is backed by Redis so the
# 5-failed-logins -> 15-minute lockout rule holds across workers.
_throttles: dict[str, LoginThrottle] = {}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_code: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _throttle_for(key: str) -> LoginThrottle:
    return _throttles.setdefault(key, LoginThrottle())


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_tenant_db),
) -> dict:
    """Authenticate a school user, enforcing lockout + optional TOTP."""
    throttle = _throttle_for(payload.email.lower())
    if throttle.is_locked():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked. Retry in {throttle.retry_after_seconds()}s",
        )

    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        locked = throttle.register_failure()
        detail = "Account locked due to repeated failures" if locked else "Invalid credentials"
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    # MFA required for Levels 1-5.
    role = rbac.Role[user.role] if user.role in rbac.Role.__members__ else None
    if role is not None and rbac.requires_mfa(role) and user.mfa_enabled:
        if not payload.totp_code or not verify_totp(user.mfa_secret or "", payload.totp_code):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA required")

    throttle.register_success()

    tenant_id = getattr(request.state, "tenant_id", None)
    perms = sorted(rbac.default_permissions_for(role)) if role else []
    fingerprint = device_fingerprint(
        request.headers.get("user-agent"), request.client.host if request.client else None
    )
    claims = {"email": user.email, "role": user.role, "tenant": tenant_id, "permissions": perms}
    tokens = TokenPair(
        access_token=create_access_token(user.id, **claims),
        refresh_token=create_refresh_token(user.id, tenant=tenant_id),
    )
    # NOTE: a LOGIN audit record (with `fingerprint`) is written by the audit
    # service here; new-device detection triggers an email notification.
    return ok(tokens.model_dump(), message="Login successful")


@router.post("/refresh")
def refresh(refresh_token: str) -> dict:
    """Exchange a valid refresh token for a new access token."""
    try:
        claims = decode_token(refresh_token)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Invalid refresh token") from exc
    if claims.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")
    access = create_access_token(claims["sub"], tenant=claims.get("tenant"))
    return ok({"access_token": access, "token_type": "bearer"})


@router.post("/logout")
def logout(user: CurrentUser = Depends(get_current_user)) -> dict:
    """Stateless logout placeholder (token revocation list lives in Redis)."""
    return ok(message="Logged out")
