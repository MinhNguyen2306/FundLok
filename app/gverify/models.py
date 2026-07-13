import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.base import Base

# Attempt statuses (app-enforced; see spec state machine). Every attempt ends
# terminal within the request that created it — PENDING only exists while the
# provider calls are in flight or after a crash mid-request.
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_FAILED = "FAILED"
TERMINAL_STATUSES = {STATUS_APPROVED, STATUS_REJECTED, STATUS_FAILED}


class GVerifyVerification(Base):
    """One GVerify eKYC verification attempt for a FundLok user.

    A retry after rejection is a new row; the newest row per user is the
    current state (same pattern as the Didit `verifications` table).
    Submitted images are never persisted — only extracted fields and the raw
    provider payloads (for audit/reconciliation).
    """

    __tablename__ = "gverify_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # "KYC" today; "KYB" reserved for the eKYB flow (future spec).
    verification_type = Column(Text, nullable=False, server_default="KYC", index=True)
    status = Column(Text, nullable=False, server_default=STATUS_PENDING)

    # GVerify transaction ids, kept for reconciliation with the provider console.
    ocr_transaction_code = Column(Text, nullable=True)
    face_transaction_code = Column(Text, nullable=True)

    # Key identity fields extracted by OCR (verbatim as GVerify returns them).
    person_number = Column(Text, nullable=True, index=True)
    full_name = Column(Text, nullable=True)
    date_of_birth = Column(Text, nullable=True)

    # Full provider payloads ({data} objects) for audit.
    ocr_data = Column(JSONB, nullable=True)
    face_data = Column(JSONB, nullable=True)

    rejection_reason = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User")

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def is_approved(self) -> bool:
        return self.status == STATUS_APPROVED
