from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResendVerificationRequest,
    RegisterResponse,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserOut,
)
from app.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE_MAX_AGE = 30 * 60  # 30 minutes
REFRESH_COOKIE_MAX_AGE = 14 * 24 * 60 * 60  # 14 days

# "Keep me signed in" marker. The refresh endpoint re-issues both auth cookies,
# so it has to know whether the user asked for a persistent session -- without
# this, a remembered session would silently degrade to a session cookie on the
# first token refresh. httpOnly like the others: only the server reads it, and
# it carries no credential, just the choice.
REMEMBER_COOKIE = "remember_session"


def _set_auth_cookies(response: Response, tokens: dict, *, remember: bool) -> None:
    """Issue the auth cookies, persistent or session-scoped.

    remember=True  -> Max-Age set, so the browser keeps the cookies across
                      restarts and the user stays signed in for the refresh
                      token's lifetime (14 days).
    remember=False -> no Max-Age, i.e. session cookies. The browser drops them
                      when it closes, which is what a user on a shared machine
                      expects when they leave the box unticked. The tokens
                      themselves are unchanged: their own expiry still applies,
                      this only controls how long the browser holds them.
    """
    access_max_age = ACCESS_COOKIE_MAX_AGE if remember else None
    refresh_max_age = REFRESH_COOKIE_MAX_AGE if remember else None

    response.set_cookie(
        key="access_token", value=tokens["access_token"],
        httponly=True, samesite="lax", secure=False, max_age=access_max_age,
    )
    response.set_cookie(
        key="refresh_token", value=tokens["refresh_token"],
        httponly=True, samesite="lax", secure=False, max_age=refresh_max_age,
    )

    if remember:
        response.set_cookie(
            key=REMEMBER_COOKIE, value="1",
            httponly=True, samesite="lax", secure=False,
            max_age=REFRESH_COOKIE_MAX_AGE,
        )
    else:
        # Clear a marker left by an earlier remembered login on this browser,
        # otherwise the next refresh would re-persist a session the user just
        # asked not to keep.
        response.delete_cookie(key=REMEMBER_COOKIE, httponly=True, samesite="lax")


@router.post("/login", response_model=UserOut)
async def simple_login(response: Response, login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user, tokens = await service.login(db, login_data)
    _set_auth_cookies(response, tokens, remember=login_data.remember_me)
    return user


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
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
    await db.commit()
    # Preserve the login-time choice: the marker cookie is the only thing that
    # survives to tell us, since the request carries no body flag here.
    remember = request.cookies.get(REMEMBER_COOKIE) == "1"
    _set_auth_cookies(response, tokens, remember=remember)
    return tokens


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # HANDOFF-02 Fix B: revoke the presented refresh token server-side, not
    # just clear the cookie -- a stolen token no longer stays valid until
    # natural expiry after the legitimate user logs out.
    refresh_token = request.cookies.get("refresh_token")
    result = await service.logout(db, refresh_token)
    await db.commit()
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    response.delete_cookie(key=REMEMBER_COOKIE, httponly=True, samesite="lax")
    return result


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.forgot_password(db, body, background_tasks)


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    return await service.reset_password(db, body, background_tasks)
