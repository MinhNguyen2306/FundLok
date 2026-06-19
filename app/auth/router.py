from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

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
def simple_login(response: Response, login_data: LoginRequest, db: Session = Depends(get_db)):
    user, tokens = service.login(db, login_data)
    _set_auth_cookies(response, tokens)
    return user


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return service.register_user(db, user, background_tasks)


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    return service.verify_email(db, token)


@router.post("/resend-verification")
def resend_verification(body: ResendVerificationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return service.resend_verification(db, body.email, background_tasks)


@router.post("/refresh", response_model=Token)
def refresh_tokens(request: Request, response: Response, body: RefreshRequest = None, db: Session = Depends(get_db)):
    refresh_token = body.refresh_token if body and body.refresh_token else request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    tokens = service.refresh_token_pair(db, refresh_token)
    db.commit()
    _set_auth_cookies(response, tokens)
    return tokens


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Logged out successfully"}


@router.post("/forgot-password")
def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    return service.forgot_password(db, body, background_tasks)


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    return service.reset_password(db, body)
