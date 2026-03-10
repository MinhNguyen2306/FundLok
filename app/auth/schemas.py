from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    phone: str | None = None
    password: str
    role: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password too long for bcrypt")
        return v


class UserOut(BaseModel):
    id: UUID  # ← change to UUID type
    email: EmailStr
    role: str
    status: str

    class Config:
        from_attributes = True  # ← enables ORM mode (auto converts SQLAlchemy objects)

    # Optional: auto-convert UUID to str in response
    @field_validator("id", mode="before")
    @classmethod
    def uuid_to_str(cls, v):
        return str(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):  # ← this class was missing or not imported
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None






