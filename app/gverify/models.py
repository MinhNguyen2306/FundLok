import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.base import Base

# Attempt statuses (app-enforced; see spec state machine). Every attempt ends
# terminal within the request that created it — PENDING only exists while the
# provider calls are in flight or after a crash mid-request. MANUAL_REVIEW
# (KYB only) is terminal for the attempt: borderline results (low OCR
# confidence, minor registry mismatches) park for an ops decision instead of
# hard-rejecting.
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_FAILED = "FAILED"
STATUS_MANUAL_REVIEW = "MANUAL_REVIEW"
TERMINAL_STATUSES = {STATUS_APPROVED, STATUS_REJECTED, STATUS_FAILED, STATUS_MANUAL_REVIEW}


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


class GVerifyKybVerification(Base):
    """One GVerify eKYB (business verification) attempt for an SME user.

    Separate from GVerifyVerification — the payload is business-shaped, not
    person-shaped. Same append-per-attempt pattern: the newest row per user is
    the current state; retries are new rows. The certificate document is never
    persisted — only the extracted fields and raw provider payloads.
    Spec: docs/specs/gverify/ekyb-kyb-verification.md
    """

    __tablename__ = "gverify_kyb_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(Text, nullable=False, server_default=STATUS_PENDING)
    # Certificate variant sent to OCR X: COMPANY | COMPANY_BRANCH | HOUSEHOLD.
    document_type = Column(Text, nullable=False)

    # GVerify transaction ids for provider reconciliation.
    ocr_transaction_code = Column(Text, nullable=True)
    tax_transaction_code = Column(Text, nullable=True)

    # Key company fields extracted by OCR X and confirmed by the tax registry.
    tax_code = Column(Text, nullable=True, index=True)
    license_code = Column(Text, nullable=True)
    business_name = Column(Text, nullable=True)
    business_type = Column(Text, nullable=True)
    company_address = Column(Text, nullable=True)
    date_of_establishment = Column(Text, nullable=True)
    charter_capital = Column(Text, nullable=True)
    representatives = Column(JSONB, nullable=True)  # OCR X representatives verbatim

    # Full provider payloads ({data} objects) for audit.
    ocr_data = Column(JSONB, nullable=True)
    tax_data = Column(JSONB, nullable=True)

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
