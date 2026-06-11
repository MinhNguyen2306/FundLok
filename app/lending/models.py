import uuid

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    legal_name = Column(Text, nullable=False)
    tax_id = Column(Text, unique=True)
    industry = Column(Text)
    address = Column(JSONB)
    incorporation_date = Column(Date)
    status = Column(
        Text,
        nullable=False,
        server_default="ACTIVE",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    ownerships = relationship("ProjectOwnership", back_populates="project", cascade="all, delete-orphan")
    loan_applications = relationship("LoanApplication", back_populates="project")


class ProjectOwnership(Base):
    __tablename__ = "project_ownerships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False, server_default="OWNER")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="ownerships")
    user = relationship("User", back_populates="project_ownerships")

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="uq_project_ownership_project_user"),)


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    purpose = Column(Text, nullable=False)
    filename = Column(Text, nullable=False)
    mime_type = Column(Text)
    status = Column(Text, nullable=False, server_default="PENDING")
    size_bytes = Column(BigInteger)
    checksum_sha256 = Column(Text)
    storage_key = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSONB)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requested_amount = Column(Numeric(15, 2), nullable=False)
    purpose = Column(Text)
    repayment_preference = Column(Text)
    status = Column(Text, nullable=False, server_default="DRAFT")
    submitted_at = Column(DateTime(timezone=True))
    decided_at = Column(DateTime(timezone=True))
    decision_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="loan_applications")
    score_runs = relationship("ScoreRun", back_populates="application")
    application_documents = relationship(
        "ApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )
    documents = relationship(
        "LoanApplicationDocument", back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationDocument(Base):
    __tablename__ = "application_documents"

    application_id = Column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), primary_key=True
    )
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="RESTRICT"), primary_key=True)

    application = relationship("LoanApplication", back_populates="application_documents")
    document = relationship("Document")


class LoanApplicationDocument(Base):
    """One row per file uploaded for a loan application (R2 object).

    The R2 key is generated server-side; original_filename is display metadata only.
    Status: PENDING (presigned, not yet verified in R2) -> UPLOADED (HEAD-checked).
    """

    __tablename__ = "loan_application_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_application_id = Column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False
    )
    document_type = Column(Text, nullable=False)
    file_key = Column(Text, unique=True, nullable=False)
    original_filename = Column(Text, nullable=False)
    content_type = Column(Text)
    file_size_bytes = Column(BigInteger)
    status = Column(Text, nullable=False, server_default="PENDING")
    uploaded_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application = relationship("LoanApplication", back_populates="documents")

    __table_args__ = (
        Index(
            "ix_loan_application_documents_app_doc_type",
            "loan_application_id",
            "document_type",
            unique=True,
        ),
    )


class ScoreRun(Base):
    __tablename__ = "score_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False)
    status = Column(Text, nullable=False, server_default="RUNNING")
    overall_score = Column(Numeric(5, 2))
    risk_grade = Column(Text)
    recommended_terms = Column(JSONB)
    factor_results = Column(JSONB)
    locked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application = relationship("LoanApplication", back_populates="score_runs")
    contracts = relationship("Contract", back_populates="score_run")


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="SET NULL"))
    score_run_id = Column(UUID(as_uuid=True), ForeignKey("score_runs.id", ondelete="SET NULL"))
    status = Column(Text, nullable=False, server_default="DRAFT")
    final_terms = Column(JSONB, nullable=False)
    signed_at = Column(DateTime(timezone=True))
    activated_at = Column(DateTime(timezone=True))
    target_amount = Column(Numeric(15, 2), nullable=False)
    funded_amount = Column(Numeric(15, 2), nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application = relationship("LoanApplication")
    score_run = relationship("ScoreRun", back_populates="contracts")
    listing = relationship("Listing", back_populates="contract", uselist=False)
    holdings = relationship("Holding", back_populates="contract")
    ledger_entries = relationship("LedgerEntry", back_populates="contract")


class Listing(Base):
    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), unique=True, nullable=False)
    target_amount = Column(Numeric(15, 2), nullable=False)
    min_ticket = Column(Numeric(12, 2))
    status = Column(Text, nullable=False, server_default="DRAFT")
    funded_amount = Column(Numeric(15, 2), nullable=False, server_default="0")
    open_at = Column(DateTime(timezone=True))
    close_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contract = relationship("Contract", back_populates="listing")
    orders = relationship("Order", back_populates="listing")


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    investor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    status = Column(Text, nullable=False, server_default="PENDING_PAYMENT")
    payment_confirmed_at = Column(DateTime(timezone=True))
    idempotency_key = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    listing = relationship("Listing", back_populates="orders")
    investor = relationship("User", back_populates="orders")


class Holding(Base):
    __tablename__ = "holdings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    investor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"))
    principal = Column(Numeric(15, 2), nullable=False)
    share_ratio = Column(Numeric(10, 8))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="holdings")
    investor = relationship("User", back_populates="holdings")

    __table_args__ = (UniqueConstraint("contract_id", "investor_id", name="uq_holding_contract_investor"),)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    type = Column(Text, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    reference = Column(Text)
    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    idempotency_key = Column(Text, unique=True, nullable=True)

    contract = relationship("Contract", back_populates="ledger_entries")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    action = Column(Text, nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    before_state = Column(JSONB)
    after_state = Column(JSONB)
    ip_address = Column(String)  # store as string; INET optional in raw DDL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
