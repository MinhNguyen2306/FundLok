from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.schemas import Token, LoginRequest, UserCreate, UserOut  
from app.auth.service import authenticate_user, create_tokens
from app.users.models import User
from app.utils.password import hash_password


router = APIRouter(prefix="/auth", tags=["auth"])

# Register stays the same (or keep your current version)

@router.post("/login", response_model=Token)
def simple_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    token = create_tokens(str(user.id))
    return token


@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    new_user = User(
        email=user.email,
        phone=user.phone,
        password_hash=hashed,
        role=user.role,
        status="ACTIVE"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user