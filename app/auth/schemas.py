import re

from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID


ALLOWED_ROLES = frozenset({"SME", "INVESTOR", "ADMIN"})
PHONE_NUMBER_PATTERN = re.compile(
    r"^(?:\+84|84|0)(?:3|5|7|8|9)\d{8}$|^\+?[1-9]\d{7,14}$"
)


class UserCreate(BaseModel):
    email: EmailStr
    phone: str | None = None
    full_name: str
    password: str
    role: str

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

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password too long for bcrypt")
        return v

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        u = v.strip().upper()
        if u not in ALLOWED_ROLES:
            raise ValueError("role must be SME, INVESTOR, or ADMIN")
        return u


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    status: str

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class TokenData(BaseModel):
    user_id: str | None = None


class ResendVerificationRequest(BaseModel):
    email: EmailStr

