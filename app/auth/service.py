import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    UserCreate,
)
from app.users.models import RefreshToken, User
from app.utils.password import hash_password, verify_password
from app.utils.jwt import (
    create_access_token,
    create_password_reset_token,
    create_verification_token,
    verify_email_token,
    verify_password_reset_token,
)
from app.utils.email import (
    send_existing_account_notice,
    send_password_reset_email,
    send_verification_email,
)
from app.utils.captcha import verify_turnstile_token
from app.core.config import settings


async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def hash_refresh_token(token: str) -> str:
    """SHA-256 of the raw refresh JWT (HANDOFF-02 Fix B).

    Deliberately NOT the argon2 hasher in app/utils/password.py: a refresh
    token is already a long, high-entropy signed JWT, not a low-entropy human
    password, so there's nothing for a slow/memory-hard hash to brute-force
    protect against -- it would only add needless CPU/memory cost on every
    single /auth/refresh call. A fast, deterministic hash for DB lookup is
    the standard approach for opaque bearer tokens (this is how GitHub/Auth0
    store API keys and session tokens for revocation checks).
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_token_pair(db: AsyncSession, user_id: UUID | str) -> dict:
    """Issue an access/refresh JWT pair and persist the refresh token (hashed)
    in `refresh_tokens` so it can be looked up, revoked, and rotated.

    Only stages the RefreshToken row via db.add(); the caller controls the
    transaction boundary (commit), matching the rest of this module.
    """
    uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(uid)}, expires_delta=access_token_expires
    )

    refresh_expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_access_token(
        data={"sub": str(uid), "typ": "refresh"},
        expires_delta=refresh_expires_delta,
    )
    expires_at = datetime.now(timezone.utc) + refresh_expires_delta
    db.add(
        RefreshToken(
            user_id=uid,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def refresh_token_pair(db: AsyncSession, refresh_token: str) -> dict:
    """Verify + rotate a refresh token (HANDOFF-02 Fix B: stateful, revocable).

    JWT signature/expiry is checked first (cheap, no DB hit for garbage
    input); the DB is then the source of truth for revocation -- missing,
    already-revoked, or expired rows are all rejected. On success the
    presented token is revoked and a new pair is issued and persisted, which
    is proper rotation with reuse detection: a revoked token can never be
    used again, including by an attacker who captured it before rotation.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )
    try:
        payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        if payload.get("typ") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    token_hash = hash_refresh_token(refresh_token)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    stored = result.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if stored is None or stored.revoked_at is not None or stored.expires_at < now:
        raise credentials_exception

    stored.revoked_at = now
    db.add(stored)

    return await create_token_pair(db, user_id)


async def logout(db: AsyncSession, refresh_token: str | None) -> dict:
    """Revoke the presented refresh token server-side (HANDOFF-02 Fix B).

    Forgiving by design: a missing, already-revoked, or unrecognized token
    still returns success -- logout should never fail just because the
    client's cookie was already gone or stale.
    """
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        stored = result.scalar_one_or_none()
        if stored is not None and stored.revoked_at is None:
            stored.revoked_at = datetime.now(timezone.utc)
            db.add(stored)
    return {"status": "success", "message": "Logged out successfully"}


def _parse_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid token details")


async def login(db: AsyncSession, login_data: LoginRequest) -> tuple[User, dict]:
    verify_turnstile_token(login_data.turnstile_token)

    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    tokens = await create_token_pair(db, user.id)
    await db.commit()
    return user, tokens


async def register_user(
    db: AsyncSession, user_in: UserCreate, background_tasks: BackgroundTasks
) -> dict:
    """Register a new user without leaking whether the email/phone already exists.

    Every branch returns the same acknowledgement, so the endpoint can't be used
    to enumerate registered accounts (mirrors forgot_password):
      - new address        -> create the user, email a verification link
      - email already taken -> email the real owner an "account exists" notice
      - phone already taken -> stay silent (no SMS channel to notify)
    """
    verify_turnstile_token(user_in.turnstile_token)

    # Uniform response for all outcomes below. Wording must not imply success or
    # failure of account creation specifically.
    ack = {
        "status": "success",
        "message": "If these details are available, a verification email has been sent.",
    }

    existing_email = (
        await db.execute(select(User).where(User.email == user_in.email))
    ).scalar_one_or_none()
    if existing_email is not None:
        # Don't create or reveal — tell the genuine owner someone used their email.
        background_tasks.add_task(send_existing_account_notice, to_email=user_in.email)
        return ack

    if user_in.phone:
        existing_phone = (
            await db.execute(select(User).where(User.phone == user_in.phone))
        ).scalar_one_or_none()
        if existing_phone is not None:
            return ack

    new_user = User(
        email=user_in.email,
        phone=user_in.phone,
        full_name=user_in.full_name,
        password_hash=hash_password(user_in.password),
        role=None,  # chosen later via PUT /users/me/role
        status="ACTIVE",
        email_verified=False,
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError:
        # Lost a race with a concurrent signup on the same email/phone (the DB
        # unique constraints are the real guard). Roll back and return the same
        # acknowledgement so the collision still isn't observable.
        await db.rollback()
        return ack
    await db.refresh(new_user)

    # Generate verification token and send verification email in background.
    token = create_verification_token(new_user.id)
    background_tasks.add_task(send_verification_email, to_email=new_user.email, token=token)

    return ack


async def verify_email(db: AsyncSession, token: str) -> dict:
    uid = _parse_user_id(verify_email_token(token))

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_verified:
        return {"status": "success", "message": "Email already verified"}

    user.email_verified = True
    await db.commit()
    return {"status": "success", "message": "Email verified successfully"}


async def resend_verification(db: AsyncSession, email: str, background_tasks: BackgroundTasks) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        # Avoid user enumeration by returning a success-like message even if user doesn't exist.
        return {"status": "success", "message": "If the email exists, a verification link has been sent."}

    if user.email_verified:
        return {"status": "success", "message": "Email already verified"}

    token = create_verification_token(user.id)
    background_tasks.add_task(send_verification_email, to_email=user.email, token=token)
    return {"status": "success", "message": "Verification link has been sent."}


async def forgot_password(db: AsyncSession, body: ForgotPasswordRequest, background_tasks: BackgroundTasks) -> dict:
    verify_turnstile_token(body.turnstile_token)

    # Same response whether or not the email exists, to avoid user enumeration.
    response = {"status": "success", "message": "If the email is registered, a password reset link has been sent."}

    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user:
        return response

    token = create_password_reset_token(user.id)
    background_tasks.add_task(send_password_reset_email, to_email=user.email, token=token)
    return response


async def reset_password(db: AsyncSession, body: ResetPasswordRequest) -> dict:
    uid = _parse_user_id(verify_password_reset_token(body.token))

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"status": "success", "message": "Password reset successfully"}
