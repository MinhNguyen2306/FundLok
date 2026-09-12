import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.base import Base


class Role(str, PyEnum):
    SME = "SME"
    INVESTOR = "INVESTOR"
    ADMIN = "ADMIN"
    SYSTEM_ADMIN = "SYSTEM_ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    phone = Column(Text, unique=True)
    password_hash = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    avatar_key = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    role = Column(Text, nullable=True)  # null until the user selects a role post-registration
    email_verified = Column(Boolean, nullable=False, server_default="false")
    status = Column(Text, nullable=False, server_default="ACTIVE")
    # Email the owner when a device we have not seen before signs in. Opt-in:
    # see migration b8d41c60ea92.
    signin_alerts_enabled = Column(Boolean, nullable=False, server_default="false")

    # When this user finished (or skipped) the first-run dashboard walkthrough.
    # NULL means they have not seen it yet.
    #
    # Server-side rather than in the browser because the walkthrough belongs to
    # the ACCOUNT, not the device: someone who onboarded on their laptop should
    # not be walked through the product again on their phone, and someone who
    # clears site data should not lose the fact either. A timestamp rather than
    # a boolean so we can tell "onboarded last year" from "onboarded today"
    # when the tour changes and we decide whether to re-run it.
    onboarding_tour_completed_at = Column(DateTime(timezone=True))

    # --- Two-factor authentication (TOTP, RFC 6238) ---
    # The base32 shared secret. Written at setup and kept even while
    # totp_enabled is false, because enrolment is two steps: the client needs a
    # stable secret to scan before it can prove possession with a code.
    #
    # Encrypted at rest by app/auth/totp_crypto.py — stored as
    # "v1:<fernet token>", never plaintext. Hashing is not an option: the server
    # must reproduce the secret to check a code, unlike the password column
    # beside it. The plaintext leaves the server exactly once, in the setup
    # response that feeds the QR code.
    totp_secret = Column(Text)
    # The gate. False until a code has been verified, so an abandoned setup
    # never locks anyone out.
    totp_enabled = Column(Boolean, nullable=False, server_default="false")
    totp_confirmed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    project_ownerships = relationship("ProjectOwnership", back_populates="user")
    orders = relationship("Order", back_populates="investor")
    holdings = relationship("Holding", back_populates="investor")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    totp_recovery_codes = relationship(
        "TotpRecoveryCode", back_populates="user", cascade="all, delete-orphan"
    )
    webauthn_credentials = relationship(
        "WebAuthnCredential", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # One sign-in, stable across rotation. Refreshing revokes this row and
    # inserts a new one, so without this a "signed-in device" would appear to
    # be a different device after every refresh. Nullable: rows issued before
    # migration a3f7c92e1b48 have none.
    session_id = Column(UUID(as_uuid=True), index=True)
    # Captured at sign-in and refreshed on use, so the security screen can
    # describe the device a user is deciding whether to revoke.
    user_agent = Column(Text)
    ip_address = Column(Text)
    last_used_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="refresh_tokens")


class TotpRecoveryCode(Base):
    """Single-use codes for the "I lost my phone" path.

    Hashed with the same Argon2 helper as passwords, for the same reason: this
    table is a set of credentials that grant a session, so a database leak must
    not hand over working codes.

    A used code is marked, never deleted — "when was a recovery code last used"
    is exactly the kind of question a compromised-account investigation asks,
    and a deleted row cannot answer it.
    """

    __tablename__ = "totp_recovery_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code_hash = Column(Text, nullable=False)
    used_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="totp_recovery_codes")


class WebAuthnCredential(Base):
    """A registered passkey.

    One row per authenticator, because a person reasonably has several — a
    phone, a laptop's Touch ID, a hardware key — and revoking a lost one must
    not lock them out of the others.

    Nothing secret is stored. A passkey's private half never leaves the
    authenticator; `public_key` is exactly that, public, and is useless to
    anyone who steals this table. That is the whole point of the mechanism and
    the reason this model needs none of the encryption that guards
    `users.totp_secret` beside it.

    `sign_count` is the authenticator's own monotonic counter. A replayed
    assertion carries a counter at or below the stored one, which is the only
    cloning signal the protocol offers — so it is persisted and checked rather
    than ignored. Note that many platform authenticators (Apple, Google)
    always report 0; a zero counter is normal and is not evidence of anything.
    """

    __tablename__ = "webauthn_credentials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Base64url of the raw credential ID, as the browser reports it. Unique
    # across all users: an authenticator must never be silently re-bound to a
    # second account.
    credential_id = Column(Text, unique=True, nullable=False, index=True)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, nullable=False, server_default="0")
    # "platform" (Face ID, Touch ID, Windows Hello) or "cross-platform" (a
    # security key). Shown in the UI so someone can tell their devices apart.
    device_type = Column(Text, nullable=True)
    backed_up = Column(Boolean, nullable=False, server_default="false")
    transports = Column(Text, nullable=True)  # comma-separated hints
    # What the person called it, or a default derived from the user agent.
    name = Column(Text, nullable=False, server_default="Passkey")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="webauthn_credentials")


class WebAuthnChallenge(Base):
    """A pending WebAuthn ceremony.

    The protocol requires every challenge to be random, short-lived and used
    exactly once — a replayed assertion against a challenge we still accept is
    the attack this guards. Stateless signed challenges would satisfy the first
    two properties and not the third, so the rows live here and are consumed.

    `user_id` is null for a login ceremony: the whole point of a discoverable
    credential is that the browser tells us who it is, so we do not know yet
    when the options are issued.
    """

    __tablename__ = "webauthn_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    challenge = Column(Text, unique=True, nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # "registration" or "authentication" — a registration challenge must never
    # be redeemable as a login.
    purpose = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
