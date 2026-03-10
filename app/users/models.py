from sqlalchemy import Column, String, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from enum import Enum as PyEnum
import uuid


class Role(str, PyEnum):
    SME = "SME"
    INVESTOR = "INVESTOR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(Enum(Role), nullable=False)
    status = Column(String, default="ACTIVE")