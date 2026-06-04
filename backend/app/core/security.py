"""Cryptographic operations: password hashing, JWT, AES-256, TOTP.

Section 10 of the brief. This module depends on third-party libraries
(passlib/bcrypt, pyjwt, cryptography, pyotp); the *policy* that decides when to
lock out or what makes a password strong lives in the dependency-free
:mod:`app.core.security_policy` so it can be unit-tested without those libs.
"""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
import pyotp
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext

from app.core.config import get_settings

# bcrypt with a configurable cost factor (>= 12 per the brief).
_settings = get_settings()
pwd_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=_settings.bcrypt_rounds
)

ACCESS_TOKEN = "access"
REFRESH_TOKEN = "refresh"


# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(password, password_hash)


# --------------------------------------------------------------------------- #
# JWT (access + refresh)
# --------------------------------------------------------------------------- #
def _create_token(subject: str, token_type: str, expires: timedelta, claims: dict) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
        **claims,
    }
    return jwt.encode(payload, _settings.secret_key, algorithm=_settings.jwt_algorithm)


def create_access_token(subject: str, **claims: Any) -> str:
    """Create a short-lived (15 min) access token. ``claims`` may carry
    ``tenant``, ``role`` and ``permissions``."""
    return _create_token(
        subject,
        ACCESS_TOKEN,
        timedelta(minutes=_settings.access_token_expire_minutes),
        claims,
    )


def create_refresh_token(subject: str, **claims: Any) -> str:
    """Create a 7-day refresh token."""
    return _create_token(
        subject,
        REFRESH_TOKEN,
        timedelta(days=_settings.refresh_token_expire_days),
        claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises ``jwt.PyJWTError`` on failure."""
    return jwt.decode(token, _settings.secret_key, algorithms=[_settings.jwt_algorithm])


# --------------------------------------------------------------------------- #
# Field-level encryption at rest (AES-256-GCM) - section 10
# --------------------------------------------------------------------------- #
def _aes_key() -> bytes:
    """Derive a 32-byte AES-256 key from the configured ENCRYPTION_KEY."""
    return hashlib.sha256(_settings.encryption_key.encode("utf-8")).digest()


def encrypt_field(plaintext: str) -> str:
    """Encrypt a sensitive field (national ID, financial data) for storage.

    Returns a urlsafe-base64 string of ``nonce || ciphertext``. A random nonce
    is used per call so identical plaintexts do not produce identical tokens.
    """
    aesgcm = AESGCM(_aes_key())
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ct).decode("ascii")


def decrypt_field(token: str) -> str:
    """Decrypt a value produced by :func:`encrypt_field`."""
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    nonce, ct = raw[:12], raw[12:]
    aesgcm = AESGCM(_aes_key())
    return aesgcm.decrypt(nonce, ct, None).decode("utf-8")


# --------------------------------------------------------------------------- #
# TOTP two-factor auth (pyotp) - section 10
# --------------------------------------------------------------------------- #
def generate_totp_secret() -> str:
    """Generate a new base32 TOTP secret for a user."""
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, account_name: str) -> str:
    """Return an otpauth:// URI for QR-code enrollment."""
    return pyotp.TOTP(secret).provisioning_uri(
        name=account_name, issuer_name="Delta Plax Education Suite"
    )


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code (allows +/- 1 time step for clock drift)."""
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def device_fingerprint(user_agent: str | None, ip_address: str | None) -> str:
    """Derive a stable device fingerprint for new-device detection."""
    basis = f"{user_agent or ''}|{ip_address or ''}"
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()
