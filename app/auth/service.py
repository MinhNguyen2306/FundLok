from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.users.models import User, Role
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token
from app.auth.schemas import UserCreate, TokenData
from datetime import timedelta
from app.core.config import settings


def create_user(db: Session, user: UserCreate):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = User(
        email=user.email,
        phone=user.phone,
        password_hash=hashed_password,
        role=Role(user.role.upper()),
        status="ACTIVE",
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_tokens(user_id: str):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}