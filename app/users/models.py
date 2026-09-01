import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func
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
