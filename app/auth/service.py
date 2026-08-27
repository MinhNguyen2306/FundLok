import hashlib
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status

from app.auth.user_agent import describe_browser, describe_device
from app.utils.email import send_new_device_signin_alert
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    UserCreate,
)
from app.lending.models import AuditLog
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
    send_password_changed_notice,
    send_password_reset_email,
    send_verification_email,
)
from app.utils.captcha import verify_turnstile_token
from app.core.config import settings


async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    # `password_hash` is nullable (OAuth accounts have none until the user sets
    # one). Reject those before passlib sees a None hash -- it would raise
    # rather than return False, turning a normal failed login into a 500.
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
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


async def create_token_pair(db: AsyncSession, user_id: UUID | str,
    *,
    session_id: UUID | None = None,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
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
    now = datetime.now(timezone.utc)
    expires_at = now + refresh_expires_delta
    db.add(
        RefreshToken(
            user_id=uid,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
            # A fresh sign-in starts a session; a rotation carries the existing
            # one forward so the device does not look new after every refresh.
            session_id=session_id or uuid4(),
            user_agent=user_agent,
            ip_address=ip_address,
            last_used_at=now,
        )
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def refresh_token_pair(
    db: AsyncSession,
    refresh_token: str,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
) -> dict:
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
    stored.last_used_at = now
    db.add(stored)

    # Same session, new token: the device keeps its identity on the security
    # screen, and the metadata follows the latest request rather than the
    # original sign-in (an IP can change mid-session).
    return await create_token_pair(
        db,
        user_id,
        session_id=stored.session_id,
        user_agent=user_agent or stored.user_agent,
        ip_address=ip_address or stored.ip_address,
    )


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


async def login(
    db: AsyncSession,
    login_data: LoginRequest,
    *,
    user_agent: str | None = None,
    ip_address: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> tuple[User, dict]:
    verify_turnstile_token(login_data.turnstile_token)

    user = await authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    # "Have we seen this device before?" is asked BEFORE the new session row is
    # written, otherwise the sign-in we are about to record would itself count
    # as prior history and no device would ever look new.
    is_new_device = await is_unseen_device(db, user.id, user_agent)

    tokens = await create_token_pair(
        db, user.id, user_agent=user_agent, ip_address=ip_address
    )
    await db.commit()

    if is_new_device and user.signin_alerts_enabled and background_tasks is not None:
        # After the commit: the alert describes a sign-in that actually
        # happened. Queued rather than awaited so a slow mail server cannot
        # make signing in feel broken.
        background_tasks.add_task(
            send_new_device_signin_alert,
            user.email,
            device=describe_device(user_agent),
            browser=describe_browser(user_agent),
            ip_address=ip_address,
        )

    return user, tokens


async def is_unseen_device(
    db: AsyncSession, user_id: UUID, user_agent: str | None
) -> bool:
    """Whether this user agent has never signed in to this account before.

    Deliberately a user-agent match, not a fingerprint: it is the only signal
    stored, it is stable for a given browser on a given machine, and the cost of
    a false "new device" is one extra email rather than a missed warning. An
    absent user agent is treated as NOT new -- an unknown client would otherwise
    alert on every single sign-in.
    """
    if not user_agent:
        return False
    result = await db.execute(
        select(RefreshToken.id)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.user_agent == user_agent,
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is None


async def list_sessions(
    db: AsyncSession, user_id: UUID, *, current_token: str | None = None
) -> list[dict]:
    """Live sign-ins for a user, newest first.

    One row per session: rotation revokes the previous row, so the unrevoked,
    unexpired rows ARE the open sessions. The row matching the caller's own
    refresh token is flagged so the UI can label it and refuse to revoke it.
    """
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.last_used_at.desc().nullslast())
    )
    rows = result.scalars().all()
    current_hash = hash_refresh_token(current_token) if current_token else None

    return [
        {
            "session_id": row.session_id,
            "user_agent": row.user_agent,
            "ip_address": row.ip_address,
            "created_at": row.created_at,
            "last_used_at": row.last_used_at,
            "current": row.token_hash == current_hash,
        }
        for row in rows
        # A pre-migration row has no session_id and cannot be addressed by the
        # revoke endpoints, so listing it would offer an action that fails.
        if row.session_id is not None
    ]


async def revoke_session(
    db: AsyncSession, user_id: UUID, session_id: UUID, *, current_token: str | None
) -> dict:
    """Revoke every live token in one session — signing that device out.

    Scoped to the caller's own user_id: a session id is a UUID, but it must
    never be usable to sign out somebody else's device.
    """
    current_hash = hash_refresh_token(current_token) if current_token else None
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.session_id == session_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    rows = result.scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Session not found")

    if current_hash is not None and any(r.token_hash == current_hash for r in rows):
        # Signing out the device you are using is logout, not session
        # management — different endpoint, and it also clears the cookies.
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke the session you are signed in with; use logout",
        )

    now = datetime.now(timezone.utc)
    for row in rows:
        row.revoked_at = now
        db.add(row)
    return {"revoked": len(rows)}


async def revoke_other_sessions(
    db: AsyncSession, user_id: UUID, *, current_token: str | None
) -> dict:
    """Sign out everywhere except here — the "I think someone else is in my
    account" button. The caller's own session is deliberately spared."""
    current_hash = hash_refresh_token(current_token) if current_token else None
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    revoked = 0
    for row in result.scalars().all():
        if current_hash is not None and row.token_hash == current_hash:
            continue
        row.revoked_at = now
        db.add(row)
        revoked += 1
    return {"revoked": revoked}


async def register_user(
    db: AsyncSession, user_in: UserCreate, background_tasks: BackgroundTasks
) -> dict:
    """Register a new user without leaking whether the email already exists.

      - new address         -> create the user, email a verification link
      - email already taken -> same acknowledgement as success, and email the
                               real owner an "account exists" notice, so the
                               endpoint can't be used to enumerate accounts
                               (mirrors forgot_password)
      - phone already taken -> reject with an explicit 400

    The phone branch is deliberately NOT anti-enumerable. It was silent between
    a333de9 and this change, which meant a legitimate signup whose number was
    already on file got the "verification email sent" screen and then nothing —
    no account, no email, no way to find out why. Product call: a user being
    able to fix their own signup beats phone-number enumeration resistance,
    which the email branch does not provide anyway once you know the address.
    """
    verify_turnstile_token(user_in.turnstile_token)

    # Shared by the "created" and "email already taken" outcomes so the two are
    # indistinguishable. Wording must not imply success or failure of account
    # creation specifically.
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

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


async def reset_password(
    db: AsyncSession, body: ResetPasswordRequest, background_tasks: BackgroundTasks
) -> dict:
    uid = _parse_user_id(verify_password_reset_token(body.token))

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    await db.commit()

    # Queued only after the commit: the notice must never describe a change
    # that didn't land. It's what makes an unauthorised reset visible to the
    # real owner while they can still act on it.
    background_tasks.add_task(send_password_changed_notice, to_email=user.email)

    return {"status": "success", "message": "Password reset successfully"}


async def list_security_events(db: AsyncSession, user_id: UUID, *, limit: int = 20):
    """Recent security-relevant audit rows for one account, newest first.

    Filtered to SESSION/AUTH entity types: the audit log also carries business
    events (score runs, contracts) which belong on an admin trail, not on a
    user's security screen.
    """
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.actor_id == user_id,
            AuditLog.entity_type.in_(("SESSION", "AUTH")),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
