import re

from pydantic import EmailStr, BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID
from app.auth.schemas import PHONE_NUMBER_PATTERN
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


# --- Avatar upload (presign -> client PUT -> confirm), stored under user/ in the bucket ---

AVATAR_MAX_SIZE = 5 * 1024 * 1024  # 5 MB

# Allowed avatar content types mapped to the extension used in the object key.
AVATAR_CONTENT_TYPE_EXTENSIONS: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


class AvatarPresignRequest(BaseModel):
    content_type: str
    size: int = Field(gt=0)


class AvatarPresignResponse(BaseModel):
    file_key: str
    upload_url: str
    expires_in: int


class AvatarConfirmRequest(BaseModel):
    file_key: str


class UserUpdateRequest(BaseModel):
    """Self-service profile update. Only fields included in the request body are
    changed (PATCH semantics). email / role / status / password are intentionally
    not editable here — they have their own flows."""

    full_name: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("full_name cannot be empty")
        return v

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone_number(cls, v):
        if v is None:
            return None
        normalized = re.sub(r"[\s().-]", "", str(v).strip())
        if not normalized:
            return None
        if not PHONE_NUMBER_PATTERN.fullmatch(normalized):
            raise ValueError(
                "phone must match +84/84/0 Vietnamese format or an international E.164 number"
            )
        return normalized