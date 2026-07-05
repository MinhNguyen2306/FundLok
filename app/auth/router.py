from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserOut,
)
from app.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE_MAX_AGE = 30 * 60  # 30 minutes
REFRESH_COOKIE_MAX_AGE = 14 * 24 * 60 * 60  # 14 days


def _set_auth_cookies(response: Response, tokens: dict) -> None:
    response.set_cookie(
        key="access_token", value=tokens["access_token"],
        httponly=True, samesite="lax", secure=False, max_age=ACCESS_COOKIE_MAX_AGE,
    )
    response.set_cookie(
        key="refresh_token", value=tokens["refresh_token"],
        httponly=True, samesite="lax", secure=False, max_age=REFRESH_COOKIE_MAX_AGE,
    )


@router.post("/login", response_model=UserOut)
async def simple_login(response: Response, login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await service.login(db, login_data)
    _set_auth_cookies(response, tokens)
    return user


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.register_user(db, user, background_tasks)


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    return await service.verify_email(db, token)


@router.post("/resend-verification")
async def resend_verification(body: ResendVerificationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.resend_verification(db, body.email, background_tasks)


@router.post("/refresh", response_model=Token)
async def refresh_tokens(request: Request, response: Response, body: RefreshRequest = None, db: AsyncSession = Depends(get_db)):
    refresh_token = body.refresh_token if body and body.refresh_token else request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    tokens = await service.refresh_token_pair(db, refresh_token)
    _set_auth_cookies(response, tokens)
    return tokens


@router.post("/logout")
async def logout(response: Response):
    # Stateless (HANDOFF-01 characterized behavior, preserved by Fix A):
    # nothing to revoke server-side yet, just clear the cookies. HANDOFF-02
    # Fix B changes this in a later commit.
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.forgot_password(db, body, background_tasks)


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    return await service.reset_password(db, body)
