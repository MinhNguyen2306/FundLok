import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


# Didit statuses are sent as title-cased strings ("Not Started", "In Progress",
# "Approved", "Declined", "In Review", "Abandoned", "Expired", "Kyc Expired",
# "Resubmitted", "Awaiting User"). We store the raw value so we stay forward
# compatible if Didit adds states, and derive "terminal" / "approved" in code.
TERMINAL_STATUSES = {"Approved", "Declined", "Expired", "Abandoned", "Kyc Expired"}


class KycVerification(Base):
    """One Didit verification session tied to a FundLok user."""

    __tablename__ = "kyc_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Didit session identifiers / artifacts.
    session_id = Column(Text, nullable=False, unique=True, index=True)
    session_number = Column(Integer, nullable=True)
    vendor_data = Column(Text, nullable=True)  # our stable id sent to Didit (= str(user_id))
    workflow_id = Column(Text, nullable=True)
    verification_url = Column(Text, nullable=True)  # where the user completes the flow

    status = Column(Text, nullable=False, server_default="Not Started")
    decision = Column(JSONB, nullable=True)  # full decision payload once available

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def is_approved(self) -> bool:
        return self.status == "Approved"


class KycWebhookEvent(Base):
    """Dedupe ledger for Didit webhook deliveries (idempotency on event_id)."""

    __tablename__ = "kyc_webhook_events"

    event_id = Column(Text, primary_key=True)
    session_id = Column(Text, nullable=True, index=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
