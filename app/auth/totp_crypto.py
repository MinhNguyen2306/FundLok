"""Encryption at rest for TOTP secrets.

WHY THIS EXISTS
A TOTP secret is a password-equivalent: anyone holding it can generate valid
codes forever, so a database leak with plaintext secrets hands over the second
factor of every enrolled account. The password column next to it is Argon2
hashed — but hashing is not an option here, because the server has to reproduce
the secret to check a code. That leaves encryption.

THE SCHEME, AND WHAT IT IS NOT
Application-level symmetric encryption with Fernet (AES-128-CBC + HMAC-SHA256,
from `cryptography`, already a pinned dependency). Stored values carry a `v1:`
prefix so a later move to envelope encryption under a KMS can be told apart
from this format and migrated row by row, without a flag day.

This protects against a stolen database — a dump, a backup, a read-replica, a
leaked `pg_dump`. It does NOT protect against an attacker who already has the
application's environment, because the key is there by definition. That is the
honest boundary of app-level encryption, and it is a real improvement over
plaintext regardless: database compromise is by far the more common of the two.

KEY MANAGEMENT
`TOTP_ENCRYPTION_KEY` is a separate secret from `SECRET_KEY` on purpose. Reusing
the JWT signing key would tie two unrelated rotation lifecycles together: you
could never rotate the JWT secret without making every enrolled authenticator
undecryptable, which means locking every 2FA user out of their account.

FAIL CLOSED
With no key configured, enrolment is refused rather than silently falling back to
plaintext. A security feature that quietly degrades is worse than one that is
plainly unavailable — you would not know which of your users were protected.

Operational gaps this does not solve, and which belong in an ADR before
production: where the key lives (Cloud Run + Secret Manager is the obvious
answer for this deployment), how it rotates, and the recovery story if it is
lost — with no key, every enrolled user must fall back to a recovery code and
re-enrol.
"""

import logging

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# What the CLIENT is told. The specific cause goes to the log instead: the
# person who needs "TOTP_ENCRYPTION_KEY is unset" is an operator reading
# stderr, and naming server configuration in an HTTP response tells a user
# — or anyone who gets a session — how the deployment is put together.
_UNAVAILABLE = "Two-factor authentication is temporarily unavailable."

# Bump alongside the format, never reuse. A stored value is `<version>:<token>`.
_VERSION = "v1"
_PREFIX = f"{_VERSION}:"


def generate_encryption_key() -> str:
    """A fresh key, for `TOTP_ENCRYPTION_KEY`.

    Ops helper:
        python -c "from app.auth.totp_crypto import generate_encryption_key as g; print(g())"
    """
    return Fernet.generate_key().decode()


def is_configured() -> bool:
    return bool(settings.TOTP_ENCRYPTION_KEY)


def _cipher() -> Fernet:
    key = settings.TOTP_ENCRYPTION_KEY
    if not key:
        # 503, not 500: the server is fine, this feature is unconfigured.
        logger.error(
            "TOTP_ENCRYPTION_KEY is unset — two-factor enrolment refused. "
            "Generate a key with app.auth.totp_crypto.generate_encryption_key()."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_UNAVAILABLE,
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:
        logger.error(
            "TOTP_ENCRYPTION_KEY is not a valid Fernet key — two-factor "
            "enrolment refused. Generate one with "
            "app.auth.totp_crypto.generate_encryption_key()."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_UNAVAILABLE,
        ) from exc


def encrypt_secret(secret: str) -> str:
    """Plaintext base32 TOTP secret -> the value stored in `users.totp_secret`."""
    return _PREFIX + _cipher().encrypt(secret.encode()).decode()


def decrypt_secret(stored: str | None) -> str | None:
    """Stored value -> plaintext secret, or None when it cannot be recovered.

    Returns None rather than raising for any unusable value — a wrong key, a
    tampered row, or a value written before encryption existed. Callers treat
    that as "no valid secret", which fails closed: the TOTP code path cannot
    match, and the account falls back to its recovery codes. That is the right
    outcome, because the alternative to a hard failure here would be a 500 on
    every login attempt for the affected user.
    """
    if not stored:
        return None
    if not stored.startswith(_PREFIX):
        # Pre-encryption plaintext. Deliberately NOT honoured: accepting it
        # would keep the weakness alive indefinitely behind a compatibility
        # branch. 2FA shipped encrypted, so the only rows that can look like
        # this are from an unreleased build; they force a re-enrolment.
        return None

    try:
        return _cipher().decrypt(stored[len(_PREFIX) :].encode()).decode()
    except (InvalidToken, HTTPException, ValueError):
        return None


def require_configured() -> None:
    """Raise the 503 if 2FA cannot be used on this server.

    Exists so the enrolment entry point can fail before generating a secret,
    without duplicating the message or the log line.
    """
    _cipher()
