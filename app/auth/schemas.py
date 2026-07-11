import re

from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID


PHONE_NUMBER_PATTERN = re.compile(
    r"^(?:\+84|84|0)(?:3|5|7|8|9)\d{8}$|^\+?[1-9]\d{7,14}$"
)


class UserCreate(BaseModel):
    # Role is intentionally NOT chosen at registration. New users are created
    # without a role and pick one later via PUT /users/me/role.
    email: EmailStr
    phone: str | None = None
    full_name: str
    password: str
    turnstile_token: str | None = None

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


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    # None until the user selects a role after registration.
    role: str | None = None
    status: str

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    """Uniform registration acknowledgement.

    Returned identically whether or not the email/phone is already in use, so
    the endpoint cannot be used to enumerate registered accounts (mirrors the
    forgot-password flow). A genuinely new address is created and emailed a
    verification link; an already-registered email receives a security notice
    instead — the submitter can't tell the two apart.
    """
    status: str = "success"
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    turnstile_token: str | None = None


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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    turnstile_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_password_length(cls, v: str):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password too long for bcrypt")
        return v

