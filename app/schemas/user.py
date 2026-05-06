# from pydantic import EmailStr, BaseModel, Field
# from typing import Optional
# from app.models import Role # Import Enum role from models.py to use in schema

# class UserCreate(BaseModel):
#     email: EmailStr
#     password: str = Field(..., min_length=8)
#     phone: Optional[str] = None
#     role: Role

# class UserResponse(BaseModel):
#     id: str
#     email: EmailStr
#     role: Role
#     status: str

#     class Config:
#         from_attributes = True