import re

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.auth.schemas import PHONE_NUMBER_PATTERN
from app.users.models import Role

# NOTE: there is deliberately no UserCreate / registration schema here.
#
# Registration binds app.auth.schemas.UserCreate, which has NO `role` field —
# new accounts are created without one and pick SME or INVESTOR later through
# PATCH /users/me/role, where RoleSelectRequest below restricts the choice.
#
# An unused `UserCreate` with a `role: Role` field used to sit at this spot. It
# was reachable from nothing, but any future endpoint bound to it would have let
# a registrant name their own role — including ADMIN and SYSTEM_ADMIN — so it
# was removed rather than left as a trap. A `UserResponse` that exposed `role`
# and `status` went with it; /users/me answers from
# app.users.service.user_me_payload instead.


# Roles a user may assign to themselves after registration. Privileged roles
# (ADMIN / SYSTEM_ADMIN) are provisioned out-of-band and are never selectable here.
SELECTABLE_ROLES = (Role.SME, Role.INVESTOR)


class RoleSelectRequest(BaseModel):
    """One-time, post-registration role selection."""
    role: Role

    @field_validator("role")
    @classmethod
    def validate_selectable_role(cls, v: Role) -> Role:
        if v not in SELECTABLE_ROLES:
            raise ValueError("role must be SME or INVESTOR")
        return v


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


class SetPasswordRequest(BaseModel):
    """Set a FIRST password from the profile page.

    Deliberately has no `current_password`: this endpoint only ever serves an
    account that has no password yet, so there is nothing to prove. *Changing*
    an existing password goes through forgot-password / reset-password instead,
    where the emailed token is the proof — which is why a session alone can
    never overwrite a password that already exists.
    """

    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        # Same 72-byte ceiling as ResetPasswordRequest — passlib silently
        # truncates beyond it, which would make two different passwords match.
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password too long")
        return v


class UserUpdateRequest(BaseModel):
    """Self-service profile update. Only fields included in the request body are
    changed (PATCH semantics). email / role / status / password are intentionally
    not editable here — they have their own flows."""

    full_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("bio")
    @classmethod
    def normalize_bio(cls, v):
        if v is None:
            return None
        v = v.strip()
        return v or None

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

class ChangePasswordRequest(BaseModel):
    """Change an existing password from an authenticated session.

    `current_password` is what makes this safe to serve off a session alone.
    /me/password (set-password) deliberately refuses accounts that already have
    one, because overwriting a password from a borrowed session would be
    account takeover; proving knowledge of the current password is the standard
    answer to exactly that, so it is required here and not optional.
    """

    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def _strong_enough(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("New password must be at least 8 characters")
        return value


class SecurityPreferencesOut(BaseModel):
    signin_alerts_enabled: bool


class SecurityPreferencesUpdate(BaseModel):
    signin_alerts_enabled: bool
