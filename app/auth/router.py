from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.schemas import Token, LoginRequest, UserCreate, UserOut, RefreshRequest
from app.auth.service import authenticate_user, create_token_pair, refresh_token_pair
from app.users.models import User
from app.utils.password import hash_password


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserOut)  # ← was Token
def simple_login(response: Response, login_data: LoginRequest, db: Session = Depends(get_db)):
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
def register(user: UserCreate, db: Session = Depends(get_db)):
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
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


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
