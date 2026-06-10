from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.schemas import Token, LoginRequest, UserCreate, UserOut, RefreshRequest, ResendVerificationRequest
from app.auth.service import authenticate_user, create_token_pair, refresh_token_pair
from app.users.models import User
from app.utils.password import hash_password
from app.utils.jwt import create_verification_token, verify_email_token
from app.utils.email import send_verification_email
import httpx
from app.core.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)  # ← was Token
def simple_login(response: Response, login_data: LoginRequest, db: Session = Depends(get_db)):
    if settings.CLOUDFLARE_TURNSTILE_SECRET_KEY:
        if not login_data.turnstile_token:
            raise HTTPException(status_code=400, detail="Turnstile token is missing")

        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
            "response": login_data.turnstile_token
        }
        try:
            with httpx.Client() as client:
                resp = client.post(verify_url, data=payload)
                result = resp.json()
                if not result.get("success"):
                    raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification failed")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Error communicating with captcha service")

    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password")
    tokens = create_token_pair(db, user.id)
    db.commit()
    response.set_cookie(key="access_token", value=tokens["access_token"],
                        httponly=True, samesite="lax", secure=False, max_age=30 * 60)
    response.set_cookie(key="refresh_token", value=tokens["refresh_token"],
                        httponly=True, samesite="lax", secure=False, max_age=14 * 24 * 60 * 60)
    return user  # ← return user, not tokens


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if settings.CLOUDFLARE_TURNSTILE_SECRET_KEY:
        if not user.turnstile_token:
            raise HTTPException(status_code=400, detail="Turnstile token is missing")

        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            "secret": settings.CLOUDFLARE_TURNSTILE_SECRET_KEY,
            "response": user.turnstile_token
        }
        try:
            with httpx.Client() as client:
                resp = client.post(verify_url, data=payload)
                result = resp.json()
                if not result.get("success"):
                    raise HTTPException(status_code=400, detail="Cloudflare Turnstile verification failed")
        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Error communicating with captcha service")

    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if user.phone and db.query(User).filter(User.phone == user.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    hashed = hash_password(user.password)
    new_user = User(
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        password_hash=hashed,
        role=user.role,
        status="ACTIVE",
        email_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate verification token and send verification email in background
    token = create_verification_token(new_user.id)
    background_tasks.add_task(send_verification_email, to_email=new_user.email, token=token)

    return new_user


@router.get("/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user_id = verify_email_token(token)
    from uuid import UUID as PyUUID
    try:
        uid = PyUUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token details")
        
    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.email_verified:
        return {"status": "success", "message": "Email already verified"}
        
    user.email_verified = True
    db.commit()
    return {"status": "success", "message": "Email verified successfully"}


@router.post("/resend-verification")
def resend_verification(body: ResendVerificationRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user:
        # Avoid user enumeration by returning a success-like message even if user doesn't exist
        return {"status": "success", "message": "If the email exists, a verification link has been sent."}
        
    if user.email_verified:
        return {"status": "success", "message": "Email already verified"}
        
    token = create_verification_token(user.id)
    background_tasks.add_task(send_verification_email, to_email=user.email, token=token)
    return {"status": "success", "message": "Verification link has been sent."}



@router.post("/refresh", response_model=Token)
def refresh_tokens(request: Request, response: Response, body: RefreshRequest = None, db: Session = Depends(get_db)):
    refresh_token = None
    if body and body.refresh_token:
        refresh_token = body.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")
        
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
        
    tokens = refresh_token_pair(db, refresh_token)
    db.commit()
    
    # Set the rotated cookies in the response
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=30 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=14 * 24 * 60 * 60,
    )
    
    return tokens


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    return {"status": "success", "message": "Logged out successfully"}
