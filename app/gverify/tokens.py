"""Short-lived handoff tokens for the phone capture flow.

A logged-in investor on desktop mints a token, encodes it in a QR, and the
phone uses it as a Bearer credential for exactly one purpose: submitting the
KYC images. Mirrors the purpose-scoped token pattern in app/utils/jwt.py
(email_verification / password_reset) but lives here — it is GVerify-specific.
"""
from datetime import timedelta

from fastapi import HTTPException
from jose import JWTError, jwt

from app.core.config import settings
from app.utils.jwt import create_access_token

_PURPOSE = "gverify_kyc_handoff"

# Long enough to scan + photograph three images, short enough that a leaked
# QR (screenshot, shoulder-surf) goes stale quickly.
HANDOFF_TTL = timedelta(minutes=10)


def create_handoff_token(user_id) -> str:
    return create_access_token(
        data={"sub": str(user_id), "purpose": _PURPOSE},
        expires_delta=HANDOFF_TTL,
    )


def verify_handoff_token(token: str) -> str:
    """Validate a handoff token and return the user id. Raises 401 otherwise."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired handoff token")
    if payload.get("purpose") != _PURPOSE:
        raise HTTPException(status_code=401, detail="Invalid or expired handoff token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired handoff token")
    return user_id
