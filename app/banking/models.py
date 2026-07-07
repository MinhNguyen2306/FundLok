"""Mock bank/e-wallet account linking (docs/specs/banking/account-linking-mock.md).

Stands in for a real Open API partner integration (Brankas or otherwise) that
is not expected to happen. This module is the seam a real integration
replaces later -- see the spec's Open Questions.
"""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID

from app.core.base import Base

ACCOUNT_TYPES = ("BANK", "EWALLET")
LINKED_ACCOUNT_STATUSES = ("ACTIVE", "REVOKED")


class LinkedAccount(Base):
    """One mock bank/e-wallet account a user has "connected". No real
    external connectivity -- linking always succeeds synchronously and only
    a masked reference is ever persisted (see spec Business Rules)."""

    __tablename__ = "linked_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_type = Column(Text, nullable=False)
    provider = Column(Text, nullable=False, server_default="MOCK")
    account_ref_masked = Column(Text, nullable=False)
    display_name = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default="ACTIVE")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
