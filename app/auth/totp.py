"""TOTP second factor: secrets, code verification, recovery codes.

Pure functions plus the challenge-token pair. No database and no request
handling, so the rules that matter (drift window, single-use recovery codes,
constant-time comparison) are testable on their own.

Why TOTP and not SMS: SMS one-time codes are interceptable by SIM swap, which is
the standard attack against exactly this product — an account that can move
money. RFC 6238 authenticator apps have no such delivery channel.
"""

import hmac
import secrets
from datetime import timedelta

import pyotp
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings
from app.utils.jwt import create_access_token
from app.utils.password import hash_password, verify_password

# The issuer shown in the authenticator app's entry, next to the account email.
TOTP_ISSUER = "FundLok"

# ±1 step of 30s. One step each way absorbs ordinary clock drift and a user who
# starts typing as the code rolls over; widening it further multiplies the codes
# valid at any instant, which is a brute-force surface, not a courtesy.
TOTP_VALID_WINDOW = 1

RECOVERY_CODE_COUNT = 8
# 10 chars of Crockford-ish base32 ≈ 50 bits. Long enough that guessing is
# hopeless, short enough to read off paper without errors.
RECOVERY_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTVWXYZ0123456789"  # no I, L, O, U
RECOVERY_CODE_LENGTH = 10

# Time to get from the password step to the code step. Long enough to fetch a
# phone, short enough that a stolen challenge token is worthless by the time it
# is found.
TOTP_CHALLENGE_TTL = timedelta(minutes=5)
_CHALLENGE_PURPOSE = "totp_challenge"


def generate_secret() -> str:
    """A fresh base32 TOTP secret."""
    return pyotp.random_base32()


def provisioning_uri(secret: str, email: str) -> str:
    """The `otpauth://` URI an authenticator app scans as a QR code."""
    return pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=TOTP_ISSUER)


def verify_code(secret: str, code: str) -> bool:
    """Whether `code` is valid for `secret` right now.

    pyotp compares in constant time internally. Non-digit input is rejected
    before it reaches pyotp so a caller cannot smuggle whitespace tricks.
    """
    if not secret or not code:
        return False

    cleaned = code.strip().replace(" ", "")
    if not cleaned.isdigit() or len(cleaned) != 6:
        return False

    return pyotp.TOTP(secret).verify(cleaned, valid_window=TOTP_VALID_WINDOW)


def generate_recovery_codes() -> list[str]:
    """Plaintext recovery codes, shown to the user exactly once."""
    return [
        "".join(
            secrets.choice(RECOVERY_CODE_ALPHABET) for _ in range(RECOVERY_CODE_LENGTH)
        )
        for _ in range(RECOVERY_CODE_COUNT)
    ]


def normalize_recovery_code(code: str) -> str:
    """Accept what a human types: spaces, dashes and lower case."""
    return code.strip().replace(" ", "").replace("-", "").upper()


def hash_recovery_code(code: str) -> str:
    return hash_password(normalize_recovery_code(code))


def recovery_code_matches(code: str, code_hash: str) -> bool:
    return verify_password(normalize_recovery_code(code), code_hash)


def create_challenge_token(user_id) -> str:
    """Proof that the password step succeeded and only the code is outstanding.

    Carries `purpose`, which app.utils.jwt.get_current_user now rejects — so
    this token cannot be used as a session. That check is what makes the second
    factor a gate rather than a suggestion: without it, this token would already
    be a fully authenticated credential and skipping the code step would be
    trivial.
    """
    return create_access_token(
        data={"sub": str(user_id), "purpose": _CHALLENGE_PURPOSE},
        expires_delta=TOTP_CHALLENGE_TTL,
    )


def verify_challenge_token(token: str) -> str:
    """Validate a challenge token and return the user id, or 401."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired two-factor challenge",
    )
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError:
        raise invalid

    # hmac.compare_digest rather than != : the purpose is attacker-supplied.
    if not hmac.compare_digest(str(payload.get("purpose") or ""), _CHALLENGE_PURPOSE):
        raise invalid
    user_id = payload.get("sub")
    if not user_id:
        raise invalid
    return user_id
