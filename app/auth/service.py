from datetime import timedelta
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy.orm import Session
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


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_token_pair(db: Session, user_id: UUID) -> dict:
    # NOTE: refresh tokens are stateless JWTs for MVP robustness.
    # This avoids DB dependencies when `refresh_tokens` table can't be created/altered.
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": str(user_id), "typ": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def refresh_token_pair(db: Session, refresh_token: str) -> dict:
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

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)}, expires_delta=access_token_expires
    )
    # Rotate refresh for better hygiene (still stateless).
    new_refresh_token = create_access_token(
        data={"sub": str(user_id), "typ": "refresh"},
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


def _parse_user_id(user_id: str) -> UUID:
    try:
        return UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid token details")


def login(db: Session, login_data: LoginRequest) -> tuple[User, dict]:
    verify_turnstile_token(login_data.turnstile_token)

    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    tokens = create_token_pair(db, user.id)
    db.commit()
    return user, tokens


def register_user(db: Session, user_in: UserCreate, background_tasks: BackgroundTasks) -> User:
    verify_turnstile_token(user_in.turnstile_token)

    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_in.phone and db.query(User).filter(User.phone == user_in.phone).first():
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
    db.commit()
    db.refresh(new_user)

    # Generate verification token and send verification email in background.
    token = create_verification_token(new_user.id)
    background_tasks.add_task(send_verification_email, to_email=new_user.email, token=token)

    return new_user


def verify_email(db: Session, token: str) -> dict:
    uid = _parse_user_id(verify_email_token(token))

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.email_verified:
        return {"status": "success", "message": "Email already verified"}

    user.email_verified = True
    db.commit()
    return {"status": "success", "message": "Email verified successfully"}


def resend_verification(db: Session, email: str, background_tasks: BackgroundTasks) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Avoid user enumeration by returning a success-like message even if user doesn't exist.
        return {"status": "success", "message": "If the email exists, a verification link has been sent."}

    if user.email_verified:
        return {"status": "success", "message": "Email already verified"}

    token = create_verification_token(user.id)
    background_tasks.add_task(send_verification_email, to_email=user.email, token=token)
    return {"status": "success", "message": "Verification link has been sent."}


def forgot_password(db: Session, body: ForgotPasswordRequest, background_tasks: BackgroundTasks) -> dict:
    verify_turnstile_token(body.turnstile_token)

    # Same response whether or not the email exists, to avoid user enumeration.
    response = {"status": "success", "message": "If the email is registered, a password reset link has been sent."}

    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        return response

    token = create_password_reset_token(user.id)
    background_tasks.add_task(send_password_reset_email, to_email=user.email, token=token)
    return response


def reset_password(db: Session, body: ResetPasswordRequest) -> dict:
    uid = _parse_user_id(verify_password_reset_token(body.token))

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"status": "success", "message": "Password reset successfully"}
