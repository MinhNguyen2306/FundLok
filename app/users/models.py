import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(str, PyEnum):
    SME = "SME"
    INVESTOR = "INVESTOR"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    phone = Column(Text, unique=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    avatar_key = Column(Text, nullable=True)
    role = Column(Text, nullable=False)
    email_verified = Column(Boolean, nullable=False, server_default="false")
    status = Column(Text, nullable=False, server_default="ACTIVE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    project_ownerships = relationship("ProjectOwnership", back_populates="user")
    orders = relationship("Order", back_populates="investor")
    holdings = relationship("Holding", back_populates="investor")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")
