from pydantic import EmailStr, BaseModel, Field
from typing import Optional
from uuid import UUID
from app.users.models import Role

class UserCreate(BaseModel):
    """Schema for user registration (FE to BE)"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = None
    role: Role

class UserResponse(BaseModel):
    """Schema for public user profile (BE to FE)"""
    id: UUID
    email: EmailStr
    role: Role
    status: str

    class Config:
        from_attributes = True