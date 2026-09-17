"""WebAuthn ceremonies for passkey registration and sign-in.

Thin wrapper over py_webauthn: this module owns the challenge lifecycle and the
database, the library owns the cryptography. Nothing here should ever verify a
signature by hand.

Two properties are load-bearing and easy to lose in a refactor:

* **A challenge is single-use.** Options are issued with a random challenge
  that is written to `webauthn_challenges`; verification consumes the row in
  the same transaction. A replayed assertion therefore finds no challenge and
  is refused. This is why challenges are rows rather than stateless signed
  blobs, which could enforce randomness and expiry but not single use.

* **The RP ID binds a credential to a domain.** A passkey registered against
  one RP ID cannot be asserted against another; the browser refuses. Changing
  `WEBAUTHN_RP_ID` therefore invalidates every passkey already registered, so
  it is derived from FRONTEND_URL rather than being free-typed per screen.
"""

from __future__ import annotations

import base64
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes
from webauthn.helpers.exceptions import (
    InvalidAuthenticationResponse,
    InvalidRegistrationResponse,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.core.config import settings
from app.users.models import User, WebAuthnChallenge, WebAuthnCredential

# Long enough to pick a device and present a finger; short enough that a
# challenge captured from a log is dead before it can be used.
CHALLENGE_TTL_SECONDS = 300

PURPOSE_REGISTRATION = "registration"
PURPOSE_AUTHENTICATION = "authentication"

# A person reasonably has a phone, a laptop and a hardware key. The cap exists
# so a bug or a script cannot grow the row set without bound.
MAX_CREDENTIALS_PER_USER = 20


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


async def _issue_challenge(
    db: AsyncSession, *, challenge: bytes, user_id, purpose: str
) -> None:
    """Record a pending ceremony, clearing any earlier one for the same user.

    Superseding rather than accumulating: a user who opens the dialog three
    times should not leave two live challenges behind that an attacker could
    still redeem.
    """
    if user_id is not None:
        await db.execute(
            delete(WebAuthnChallenge).where(
                WebAuthnChallenge.user_id == user_id,
                WebAuthnChallenge.purpose == purpose,
            )
        )
    db.add(
        WebAuthnChallenge(
            challenge=_b64(challenge),
            user_id=user_id,
            purpose=purpose,
            expires_at=datetime.now(timezone.utc)
            + timedelta(seconds=CHALLENGE_TTL_SECONDS),
        )
    )
    await db.commit()


async def _consume_challenge(
    db: AsyncSession, *, challenge_b64: str, purpose: str
) -> WebAuthnChallenge:
    """Take a pending challenge, or refuse. Single-use is enforced here."""
    row = (
        await db.execute(
            select(WebAuthnChallenge).where(
                WebAuthnChallenge.challenge == challenge_b64,
                WebAuthnChallenge.purpose == purpose,
            )
        )
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This request has expired. Please try again.",
        )

    expired = row.expires_at < datetime.now(timezone.utc)
    # Deleted either way: an expired challenge has no further use, and leaving
    # it behind is how a table becomes a graveyard.
    await db.delete(row)
    await db.commit()

    if expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This request has expired. Please try again.",
        )
    return row


async def credentials_for_user(
    db: AsyncSession, user_id
) -> list[WebAuthnCredential]:
    result = await db.execute(
        select(WebAuthnCredential)
        .where(WebAuthnCredential.user_id == user_id)
        .order_by(WebAuthnCredential.created_at.desc())
    )
    return list(result.scalars().all())


async def delete_credential(
    db: AsyncSession, user: User, credential_id
) -> WebAuthnCredential:
    """Remove one passkey.

    Scoped to the caller's own rows, so a guessed id belonging to another
    account reads as "not found" rather than deleting someone else's key.

    Deliberately allows removing the LAST passkey: a passkey is an additional
    way in, never the only one — the account still has its password and, where
    enrolled, TOTP. Refusing here would strand someone whose only authenticator
    was a phone they no longer have.
    """
    row = (
        await db.execute(
            select(WebAuthnCredential).where(
                WebAuthnCredential.id == credential_id,
                WebAuthnCredential.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Passkey not found."
        )
    await db.delete(row)
    await db.flush()
    return row


# --------------------------------------------------------------------------
# Registration — adding a passkey to an account that is already signed in
# --------------------------------------------------------------------------


async def registration_options(db: AsyncSession, user: User) -> str:
    existing = await credentials_for_user(db, user.id)
    if len(existing) >= MAX_CREDENTIALS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have reached the maximum number of passkeys.",
        )

    options = generate_registration_options(
        rp_id=settings.webauthn_rp_id,
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.email,
        user_display_name=user.full_name or user.email,
        # Excluding what is already registered makes the authenticator say
        # "you already have one of these" instead of silently creating a
        # duplicate the user then has to tell apart in the list.
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.credential_id))
            for c in existing
        ],
        authenticator_selection=AuthenticatorSelectionCriteria(
            # Discoverable so sign-in can start from nothing but a tap — no
            # email typed first. That is the experience the feature is for.
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    await _issue_challenge(
        db, challenge=options.challenge, user_id=user.id, purpose=PURPOSE_REGISTRATION
    )
    return options_to_json(options)


async def verify_registration(
    db: AsyncSession, user: User, credential: dict, name: str | None
) -> WebAuthnCredential:
    challenge_b64 = _expected_challenge(credential)
    row = await _consume_challenge(
        db, challenge_b64=challenge_b64, purpose=PURPOSE_REGISTRATION
    )
    if row.user_id != user.id:
        # The challenge belongs to somebody else's ceremony.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This request has expired. Please try again.",
        )

    try:
        verified = verify_registration_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge_b64),
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origins,
        )
    except InvalidRegistrationResponse as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That passkey could not be verified.",
        ) from exc

    credential_id = _b64(verified.credential_id)
    clash = (
        await db.execute(
            select(WebAuthnCredential).where(
                WebAuthnCredential.credential_id == credential_id
            )
        )
    ).scalar_one_or_none()
    if clash is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That passkey is already registered.",
        )

    row = WebAuthnCredential(
        user_id=user.id,
        credential_id=credential_id,
        public_key=_b64(verified.credential_public_key),
        sign_count=verified.sign_count,
        device_type=getattr(verified.credential_device_type, "value", None),
        backed_up=bool(verified.credential_backed_up),
        transports=",".join(credential.get("transports") or []) or None,
        name=(name or "").strip()[:80] or "Passkey",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


# --------------------------------------------------------------------------
# Authentication — signing in with a passkey, no password
# --------------------------------------------------------------------------


async def authentication_options(db: AsyncSession) -> str:
    """Options for a discoverable-credential sign-in.

    No `allow_credentials`: the browser offers whichever passkeys it holds for
    this RP and tells us who it is afterwards. Sending a list would require
    knowing the account first, which would both defeat the point and let an
    unauthenticated caller enumerate which emails have passkeys.
    """
    options = generate_authentication_options(
        rp_id=settings.webauthn_rp_id,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    await _issue_challenge(
        db, challenge=options.challenge, user_id=None, purpose=PURPOSE_AUTHENTICATION
    )
    return options_to_json(options)


async def verify_authentication(
    db: AsyncSession, credential: dict
) -> tuple[User, WebAuthnCredential]:
    challenge_b64 = _expected_challenge(credential)
    await _consume_challenge(
        db, challenge_b64=challenge_b64, purpose=PURPOSE_AUTHENTICATION
    )

    raw_id = credential.get("rawId") or credential.get("id")
    if not raw_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed passkey response."
        )
    stored = (
        await db.execute(
            select(WebAuthnCredential).where(
                WebAuthnCredential.credential_id == _normalise(raw_id)
            )
        )
    ).scalar_one_or_none()
    if stored is None:
        # Same message as a failed signature: whether a given passkey is known
        # is not something an unauthenticated caller gets to learn.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That passkey was not recognised.",
        )

    try:
        verified = verify_authentication_response(
            credential=credential,
            expected_challenge=base64url_to_bytes(challenge_b64),
            expected_rp_id=settings.webauthn_rp_id,
            expected_origin=settings.webauthn_origins,
            credential_public_key=base64url_to_bytes(stored.public_key),
            credential_current_sign_count=stored.sign_count,
        )
    except InvalidAuthenticationResponse as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That passkey was not recognised.",
        ) from exc

    user = (
        await db.execute(select(User).where(User.id == stored.user_id))
    ).scalar_one_or_none()
    if user is None or user.status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That passkey was not recognised.",
        )

    stored.sign_count = verified.new_sign_count
    stored.last_used_at = datetime.now(timezone.utc)
    db.add(stored)
    await db.commit()
    return user, stored


def _normalise(raw_id: str) -> str:
    """Strip base64url padding so lookups match what registration stored."""
    return raw_id.rstrip("=")


def _expected_challenge(credential: dict) -> str:
    """Read the challenge the authenticator signed, from clientDataJSON.

    Read rather than trusted: it only selects which pending ceremony this is.
    The library independently re-checks that this value matches what it was
    given, so a forged clientDataJSON buys nothing but a missing challenge row.
    """
    try:
        client_data = credential["response"]["clientDataJSON"]
        decoded = base64url_to_bytes(client_data)
        import json

        return json.loads(decoded)["challenge"].rstrip("=")
    except Exception as exc:  # malformed input from an unauthenticated caller
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed passkey response.",
        ) from exc
