import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID as PyUUID

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.auth.schemas import TokenData
from app.users.models import User

# HTTPBearer parses Authorization: Bearer <token> reliably for API clients (curl, Postman).
http_bearer = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Bug found + fixed under HANDOFF-02 Fix B: this previously encoded only
    the caller's claims plus an integer `exp`. `exp` has one-second
    resolution, so two tokens minted for the same user+claims within the same
    wall-clock second (e.g. register -> immediately login, or refresh called
    twice back-to-back) were byte-for-byte identical JWTs. That was invisible
    before Fix B, since stateless refresh tokens were never persisted or
    deduped -- but refresh_tokens.token_hash is UNIQUE, so identical tokens
    now fail to insert with an IntegrityError. A `jti` (JWT ID) claim
    guarantees every issued token is unique regardless of timing, which is
    the standard fix for this class of bug.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    # Integer exp avoids python-jose / client decode edge cases with datetime objects.
    to_encode.update({"exp": int(expire.timestamp()), "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: AsyncSession = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials.strip()
        
    if not token:
        token = request.cookies.get("access_token")
        
    if not token:
        raise credentials_exception
        
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    try:
        uid = PyUUID(str(token_data.user_id))
    except (ValueError, TypeError):
        raise credentials_exception
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def create_verification_token(user_id: str) -> str:
    return create_access_token(
        data={"sub": str(user_id), "purpose": "email_verification"},
        expires_delta=timedelta(hours=24)
    )


def verify_email_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        if payload.get("purpose") != "email_verification":
            raise HTTPException(status_code=400, detail="Invalid token purpose")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token claim")
        return user_id
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")


def create_password_reset_token(user_id: str) -> str:
    return create_access_token(
        data={"sub": str(user_id), "purpose": "password_reset"},
        expires_delta=timedelta(hours=1)
    )


def verify_password_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": False},
        )
        if payload.get("purpose") != "password_reset":
            raise HTTPException(status_code=400, detail="Invalid token purpose")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid token claim")
        return user_id
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")