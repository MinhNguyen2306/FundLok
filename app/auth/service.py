from datetime import timedelta
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks, HTTPException, status

from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
    UserCreate,
)
from app.users.models import User
from app.utils.password import hash_password, verify_password
from app.utils.jwt import (
    create_access_token,
    create_password_reset_token,
    create_verification_token,
    verify_email_token,
    verify_password_reset_token,
)
from app.utils.email import send_password_reset_email, send_verification_email
from app.utils.captcha import verify_turnstile_token
from app.core.config import settings


async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def create_token_pair(db: AsyncSession, user_id: UUID | str) -> dict:
    """Issue an access/refresh JWT pair.

    Stateless (HANDOFF-01 characterized behavior, preserved as-is by Fix A):
    refresh tokens are signed JWTs only, never persisted -- there is no
    server-side revocation yet. `db` is accepted (and unused) purely to keep
    this signature stable across HANDOFF-02 Fix B, which adds persistence
    here in a later commit.
    """
    uid = user_id if isinstance(user_id, UUID) else UUID(str(user_id))

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(uid)}, expires_delta=access_token_expires
    )

    refresh_token = create_access_token(
        data={"sub": str(uid), "typ": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


async def refresh_token_pair(db: AsyncSession, refresh_token: str) -> dict:
    """Verify a refresh JWT and issue a new pair.

    Stateless (HANDOFF-01 characterized behavior): only the JWT
    signature/expiry/claims are checked -- there is no revocation list, so a
    still-valid (unexpired) refresh token can be used to mint new pairs
    indefinitely. HANDOFF-02 Fix B changes this in a later commit.
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

    return await create_token_pair(db, user_id)


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


async def register_user(db: AsyncSession, user_in: UserCreate, background_tasks: BackgroundTasks) -> User:
    verify_turnstile_token(user_in.turnstile_token)

    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_in.phone:
        result = await db.execute(select(User).where(User.phone == user_in.phone))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone number already registered")

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
    await db.commit()
    await db.refresh(new_user)

    # Generate verification token and send verification email in background.
    token = create_verification_token(new_user.id)
    background_tasks.add_task(send_verification_email, to_email=new_user.email, token=token)

    return new_user


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
