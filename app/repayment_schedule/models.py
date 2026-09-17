"""Fixed daily repayment mechanism -- data model (T6, HANDOFF-03).

Spec: docs/specs/repayment_schedule/facility-data-model.md
Source-of-record inputs: "FundLok Fixed Daily Repayment Mechanism Spec
v1.3" (Loc) -- referenced throughout HANDOFF-03 as spec sections
§4.1/§4.5/§5/§6/§8/§10/§11, and the repayment-model decision record
(12 Aug 2026): fixed total obligation + fixed % of daily revenue,
collected until satisfied, duration = max(contractual term, actual time
to satisfy). See that spec doc's "Open Questions" section for the one
formula (the backstop day-index calculation, §4.5) this handoff could not
locate in the repo and flagged back to Edward rather than guessing at.

Five tables per HANDOFF-03 T6 (S4 scope: no `revenue_submission`,
`extension`, or `fee_ledger` -- extensions are out of MVP):

    facility           -- one row per disbursed contract on a fixed schedule
    schedule_version   -- the generated schedule (v1 always has exactly one
                          per facility; the seam a later extension spec
                          would use to version a re-spread schedule, S4)
    scheduled_payment   -- one row per expected business-day instalment
    inbound_transfer   -- bank statement lines (S2: statement-export-only,
                          matched to a facility by payment_reference, D20)
    state_transition   -- append-only audit trail of every facility state
                          change (mirrors the ledger's append-only pattern)

All money is `Numeric(20,0)` (T1 -- integer VND, no sub-unit).
"""
import uuid

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.base import Base

# Facility state machine (T9, spec §5.3). UNDER_REVIEW is explicitly
# omitted per S4.
FACILITY_STATES = (
    "DRAFT",
    "APPROVED",
    "DISBURSED",
    "ACTIVE",
    "ARREARS_WARNING",
    "ARREARS",
    "ACCELERATED",
    "IN_RECOVERY",
    "SETTLED",
    "WRITTEN_OFF",
)

SCHEDULED_PAYMENT_STATUSES = ("PENDING", "SATISFIED", "MISSED")

# S2: bank gives statement export only; push-only collection reconciled
# against payment_reference (D20), never amount or payer name.
INBOUND_TRANSFER_STATUSES = ("UNMATCHED", "MATCHED", "APPLIED")


class Facility(Base):
    """One row per contract once it is on a fixed daily-repayment schedule.

    Terms are fixed at origination (T7): `total_obligation_vnd` and
    `daily_repayment_rate` never change after ACTIVE (S4 -- no
    re-amortization, no extensions in v1). `backstop_day_index` is the
    "whichever is longer" ceiling (repayment-model-decision, "STILL OPEN:
    there is a floor but no ceiling" -- resolved by the still-missing
    backstop formula, spec §4.5); it is set exactly once at origination and
    is immutable at the DB layer (INV-10) via the guard trigger in this
    migration -- not just append-only in application code.
    """

    __tablename__ = "facility"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id = Column(UUID(as_uuid=True), ForeignKey("contracts.id", ondelete="RESTRICT"), nullable=False, unique=True)

    # Origination inputs (spec §4.1 variables: P, r, x).
    principal_vnd = Column(Numeric(20, 0), nullable=False)
    annual_rate_pct = Column(Numeric(6, 3), nullable=False)
    contractual_term_months = Column(Integer, nullable=False)

    # Origination outputs, fixed for the life of the facility (S4).
    interest_vnd = Column(Numeric(20, 0), nullable=False)  # I
    total_obligation_vnd = Column(Numeric(20, 0), nullable=False)  # T0 = P + I

    # "Whichever is longer" (repayment-model-decision): N0 is the
    # contractual business-day count; backstop_day_index (N_bs) is the
    # ceiling past which acceleration is evaluated (T9 INV-4/INV-9).
    business_day_count = Column(Integer, nullable=False)  # N0
    backstop_day_index = Column(Integer, nullable=True)  # N_bs -- immutable once set (INV-10)
    backstop_date = Column(Date, nullable=True)  # derived from backstop_day_index via the calendar (T8, EC-15)

    status = Column(Text, nullable=False, server_default="DRAFT")

    # D20: bank statement lines are matched to a facility by this field
    # alone -- never amount or payer name (T10, out of scope here, but the
    # column and its uniqueness are part of the data model T6 builds).
    payment_reference = Column(Text, nullable=False, unique=True)

    disbursed_at = Column(DateTime(timezone=True), nullable=True)
    cure_period_ends = Column(DateTime(timezone=True), nullable=True)  # set on ACCELERATED (T11, §6.3)

    # Running projections T10/T11 maintain going forward. Not append-only --
    # these are current-state summaries, distinct from the append-only
    # scheduled_payment/state_transition/ledger tables that back them.
    collected_to_date_vnd = Column(Numeric(20, 0), nullable=False, server_default="0")
    arrears_balance_vnd = Column(Numeric(20, 0), nullable=False, server_default="0")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    contract = relationship("Contract")
    schedule_versions = relationship("ScheduleVersion", back_populates="facility", cascade="all, delete-orphan")
    scheduled_payments = relationship("ScheduledPayment", back_populates="facility", cascade="all, delete-orphan")
    inbound_transfers = relationship("InboundTransfer", back_populates="facility")
    state_transitions = relationship("StateTransition", back_populates="facility", cascade="all, delete-orphan")


class ScheduleVersion(Base):
    """The generated schedule for a facility (spec §4.1). Exactly one row
    per facility under S4 (no extensions -> no re-spread -> no second
    version) -- versioned anyway because re-amortization (§4.2, explicitly
    out of scope) is the only thing that would ever create a second row,
    and that seam is cheaper to leave in the schema now than to retrofit
    once real schedule data exists (same reasoning as T1's timing).
    """

    __tablename__ = "schedule_version"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facility.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False, server_default="1")

    daily_amount_vnd = Column(Numeric(20, 0), nullable=False)  # A0 -- floor(T0 / N0)
    day_count = Column(Integer, nullable=False)  # N0
    remainder_vnd = Column(Numeric(20, 0), nullable=False)  # T0 - A0*N0, absorbed entirely by the final instalment
    final_instalment_vnd = Column(Numeric(20, 0), nullable=False)  # A0 + remainder

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    facility = relationship("Facility", back_populates="schedule_versions")
    scheduled_payments = relationship("ScheduledPayment", back_populates="schedule_version")

    __table_args__ = (
        UniqueConstraint("facility_id", "version_number", name="uq_schedule_version_facility_version"),
    )


class ScheduledPayment(Base):
    """One expected business-day instalment (spec §4.1/§8). `expected_amount_vnd`
    is `daily_amount_vnd` for every day except the last in its schedule
    version, which carries `final_instalment_vnd` (remainder absorption).
    """

    __tablename__ = "scheduled_payment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facility.id", ondelete="CASCADE"), nullable=False)
    schedule_version_id = Column(
        UUID(as_uuid=True), ForeignKey("schedule_version.id", ondelete="CASCADE"), nullable=False
    )

    day_index = Column(Integer, nullable=False)  # 1-based position within the schedule
    scheduled_date = Column(Date, nullable=False)  # concrete business-day date (T8 calendar)
    expected_amount_vnd = Column(Numeric(20, 0), nullable=False)

    status = Column(Text, nullable=False, server_default="PENDING")
    satisfied_amount_vnd = Column(Numeric(20, 0), nullable=False, server_default="0")
    satisfied_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    facility = relationship("Facility", back_populates="scheduled_payments")
    schedule_version = relationship("ScheduleVersion", back_populates="scheduled_payments")

    __table_args__ = (
        # INV-6: no two scheduled payments on the same facility share a date.
        UniqueConstraint("facility_id", "scheduled_date", name="uq_scheduled_payment_facility_date"),
        UniqueConstraint("facility_id", "day_index", name="uq_scheduled_payment_facility_day_index"),
    )


class InboundTransfer(Base):
    """One bank statement line (S2: statement-export-only; T10, out of
    scope here beyond the data model). `external_transaction_id` is the
    bank's own unique id for the line and is the sole idempotency key
    (INV-12/EC-18) -- enforced at the DB level via UNIQUE, never in
    application code alone, per HANDOFF-03's explicit instruction.
    `facility_id` is nullable because a transfer is matched to a facility
    by `payment_reference` (D20) only after import; an unmatched or
    ambiguous transfer stays `UNMATCHED` rather than being discarded or
    auto-applied on a best guess (EC-11).
    """

    __tablename__ = "inbound_transfer"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facility.id", ondelete="RESTRICT"), nullable=True)

    source = Column(Text, nullable=False)  # e.g. "CSV_IMPORT" (S2's manual-CSV StatementSource impl)
    external_transaction_id = Column(Text, nullable=False)  # the bank's own natural key
    bank_reference = Column(Text, nullable=False)  # matched against facility.payment_reference
    amount_vnd = Column(Numeric(20, 0), nullable=False)
    value_date = Column(Date, nullable=False)

    status = Column(Text, nullable=False, server_default="UNMATCHED")
    attributed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    attributed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    facility = relationship("Facility", back_populates="inbound_transfers")

    __table_args__ = (
        # INV-12/EC-18: re-importing the same statement line must not
        # create a second row or double-credit -- enforced at the DB level.
        UniqueConstraint("external_transaction_id", name="uq_inbound_transfer_external_transaction_id"),
    )


class StateTransition(Base):
    """Append-only audit trail of every facility state change (T9). Mirrors
    the ledger's append-only pattern (ADR-002): a BEFORE UPDATE/DELETE
    trigger in this migration forbids mutation. Corrections are new,
    self-explanatory rows (e.g. a system-triggered reversal), never an
    edit of history.
    """

    __tablename__ = "state_transition"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("facility.id", ondelete="CASCADE"), nullable=False)

    from_status = Column(Text, nullable=True)  # NULL only for the first transition (-> DRAFT)
    to_status = Column(Text, nullable=False)
    trigger = Column(Text, nullable=False)  # e.g. "ADMIN_APPROVE", "DISBURSEMENT_POSTED", "CUTOFF_BATCH"
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)  # NULL for system/batch triggers
    metadata_ = Column("metadata", JSONB, nullable=True)

    occurred_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    facility = relationship("Facility", back_populates="state_transitions")
