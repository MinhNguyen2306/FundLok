from pydantic import BaseModel, EmailStr, Field

class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    # The form has always sent a subject; it used to be dropped silently here.
    subject: str | None = Field(default=None, max_length=300)
    message: str = Field(min_length=1, max_length=5000)
    turnstile_token: str | None = None
