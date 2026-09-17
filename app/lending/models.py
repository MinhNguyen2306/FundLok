import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.base import Base


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
    requested_amount = Column(Numeric(20, 0), nullable=False)
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


class LoanApplicationFinancials(Base):
    """The current financial picture for one loan application -- the raw
    material a `GradingInput` (app/underwriting/grading/types.py) is
    assembled from (T3). Mutable/upsert (unlike `score_run_inputs`, the
    immutable snapshot taken AT SCORING TIME): an SME's revenue history,
    AI scores, CIC result and KYC/AML outcome are collected progressively
    as document ingest/AI grading complete (out of this handoff's scope,
    per grading's own types.py docstring), and this row reflects the
    latest state.

    No endpoint here belongs to a self-service SME intake flow (that is
    `app/loans/`, Phat's) -- this handoff exposes only an admin-facing
    upsert (`PUT /underwriting/applications/{id}/financials`) so
    start_score_run() has something real to grade, since none existed
    anywhere in the codebase before T3.

    `industry`/`company_size`/`duration_months` are NOT NULL: they are
    config/input parameters `grade()`'s `_validate_inputs` checks
    regardless of data sufficiency (allowed duration set, industry
    recognised), not missing-data states (R8). Financial history fields
    are nullable -- absence there is exactly what produces
    INSUFFICIENT_DATA, not an error.
    """

    __tablename__ = "loan_application_financials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(
        UUID(as_uuid=True), ForeignKey("loan_applications.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    industry = Column(Text, nullable=False)
    company_size = Column(Text, nullable=False)
    duration_months = Column(Integer, nullable=False)
    operating_months = Column(Integer, nullable=False)

    # 24 months, m1..m24, in order. NULL elements are how a missing month
    # is represented (R8) -- the whole column is nullable so an
    # application with no revenue history submitted yet stores no array
    # at all, rather than an array of 24 NULLs.
    monthly_revenue_vnd = Column(ARRAY(Numeric(20, 0)))

    cogs_y1_vnd = Column(Numeric(20, 0))
    fixed_cost_y1_vnd = Column(Numeric(20, 0))
    variable_cost_excl_cogs_y1_vnd = Column(Numeric(20, 0))

    conc_top1_pct = Column(Float)
    conc_top3_pct = Column(Float)
    crr = Column(Float)
    rri = Column(Float)
    tcp = Column(Float)

    # Overrides only (R6, sector-reference-table.md) -- normally left
    # NULL and resolved from the sector reference table (T3) at scoring
    # time using `industry` above.
    sector_cagr_pct_override = Column(Float)
    ai_score_regulatory_override = Column(Float)
    ai_score_input_cost_vol_override = Column(Float)
    ai_score_cyclicality_override = Column(Float)
    ai_score_competitor_override = Column(Float)
    ai_score_macro_override = Column(Float)
    ai_score_uncontrollable_override = Column(Float)
    ai_score_founder_override = Column(Float)

    owner_withdrawal = Column(Float)
    cic_score = Column(Integer)
    kyc_aml_passed = Column(Boolean)
    fraud_flags = Column(ARRAY(Text), nullable=False, server_default="{}")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    application = relationship("LoanApplication", backref="financials", uselist=False)


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
    status = Column(Text, nullable=False, server_default="RUNNING")  # RUNNING | READY | LOCKED | FAILED -- run lifecycle, unchanged by T4
    overall_score = Column(Numeric(5, 2))  # legacy 2dp display value (D24) -- kept for back-compat; see final_grade_precise for the real value
    risk_grade = Column(Text)  # D23: requirements are "0-100 nominal, no letter grades" -- never written by this handoff; kept untouched (empty) per D23
    recommended_terms = Column(JSONB)
    factor_results = Column(JSONB)
    locked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # --- T4: score-run persistence and replay ---
    # `decision` is the grading OUTCOME (APPROVED|REVIEW|REJECT|INSUFFICIENT_DATA|AI_PENDING,
    # spec §5.1) -- distinct from `status` above, which is the run's own
    # lifecycle. HANDOFF-03's T4 text says "extend ScoreRun.status with
    # INSUFFICIENT_DATA and AI_PENDING", but §5.1's resolved ScoreRunOut
    # shape lists `status` and `decision` as two separate top-level fields;
    # this follows §5.1 (the more specific, later-resolved contract) rather
    # than overloading the lifecycle column -- see grading-engine spec 2
    # for the reconciliation note.
    decision = Column(Text)
    engine_version = Column(Text)
    params_version = Column(Text)
    sector_reference_version = Column(Text)
    final_grade_precise = Column(Float)  # D24: full precision, never truncated to 2dp
    interest_rate_pct = Column(Float)
    bank_rate_pct = Column(Numeric(6, 4))
    bank_rate_effective_from = Column(Date)

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
    target_amount = Column(Numeric(20, 0), nullable=False)
    funded_amount = Column(Numeric(20, 0), nullable=False, server_default="0")
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
    target_amount = Column(Numeric(20, 0), nullable=False)
    min_ticket = Column(Numeric(20, 0))
    status = Column(Text, nullable=False, server_default="DRAFT")
    funded_amount = Column(Numeric(20, 0), nullable=False, server_default="0")
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
    amount = Column(Numeric(20, 0), nullable=False)
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
    principal = Column(Numeric(20, 0), nullable=False)
    share_ratio = Column(Numeric(10, 8))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="holdings")
    investor = relationship("User", back_populates="holdings")

    __table_args__ = (UniqueConstraint("contract_id", "investor_id", name="uq_holding_contract_investor"),)


# LedgerEntry moved to app/ledger/models.py (double-entry foundation, ADR-003
# custodial/ledger account model). Re-exported here so existing imports
# (`from app.lending.models import LedgerEntry`) keep working; the
# `Contract.ledger_entries` relationship above resolves it by class name
# via the shared SQLAlchemy registry regardless of which module defines it.
from app.ledger.models import LedgerEntry  # noqa: E402,F401


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
