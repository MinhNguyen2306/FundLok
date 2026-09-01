import re

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator
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
    # "Keep me signed in". Defaults to False: a client that does not send it
    # gets session cookies, which is the safer of the two behaviours.
    remember_me: bool = False


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



class SessionOut(BaseModel):
    """One live sign-in, as the security screen renders it.

    `device` and `browser` are parsed from the stored user agent rather than
    stored separately: the UA string is the raw fact, the split is presentation
    and can be improved without a migration.
    """

    session_id: UUID
    device: str
    browser: str
    ip_address: str | None
    created_at: datetime | None
    last_used_at: datetime | None
    current: bool


class SecurityEventOut(BaseModel):
    """An entry in the account's security history, from `audit_logs`."""

    id: UUID
    action: str
    entity_type: str
    severity: str
    ip_address: str | None
    created_at: datetime | None


# --- Two-factor authentication (TOTP) --------------------------------------- #


class TotpChallengeOut(BaseModel):
    """Returned by POST /auth/login when the account has 2FA enabled.

    Carries no session: the caller must exchange `challenge_token` plus a code
    at POST /auth/login/2fa. `totp_required` is a Literal so this can sit in a
    union with UserOut without either shape being ambiguous.
    """

    totp_required: Literal[True] = True
    challenge_token: str


class TotpLoginRequest(BaseModel):
    challenge_token: str
    code: str = Field(min_length=1, max_length=64)
    # Carried over from step one: the challenge token is not the place for a UI
    # preference, and the client already knows what the user ticked.
    remember_me: bool = False


class TotpSetupOut(BaseModel):
    """The one and only time the secret leaves the server."""

    secret: str
    provisioning_uri: str


class TotpEnableRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class TotpEnableOut(BaseModel):
    """Recovery codes are returned exactly once, at enrolment.

    They are stored hashed, so there is no endpoint that can show them again —
    losing them means regenerating, which is deliberate.
    """

    enabled: bool
    recovery_codes: list[str]


class TotpDisableRequest(BaseModel):
    password: str
    # A live code or a recovery code; the service accepts either.
    code: str = Field(min_length=1, max_length=64)


class TotpStatusOut(BaseModel):
    enabled: bool
    confirmed_at: datetime | None = None
    recovery_codes_remaining: int
