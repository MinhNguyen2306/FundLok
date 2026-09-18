"""ORM models owned by underwriting (T4, HANDOFF-03).

Per CLAUDE.md's carry-forward convention, the original 12 MVP models live
in `app/lending/models.py` / `app/users/models.py`; new domain modules that
own their own tables (e.g. `app/repayment_schedule/models.py`, T6) get
their own `models.py`, imported into `app/models/__init__.py` alongside
the rest. This module follows that established pattern.

    bank_rate_config    -- T0b: bank_rate_pct is a board-set constant with
                            an effective date, not a GradingInput dataclass
                            default. Revised at scheduled reviews.
    score_run_inputs    -- T4: the exact structured GradingInput used for
                            one score run, append-only, so a past grade is
                            replayable (grade() re-run against the stored
                            inputs + engine_version + params_version +
                            sector_reference_version must reproduce the
                            same result).
"""
import uuid

from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.base import Base


class BankRateConfig(Base):
    """T0b: the board-set bank rate, with an effective date. The rate in
    force at any moment is the row with the greatest `effective_from` that
    is `<= as_of`. Rows are not deleted or edited in place -- a rate
    change is a new row, so historical score runs remain traceable to the
    exact rate that was in force when they ran."""

    __tablename__ = "bank_rate_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_pct = Column(Numeric(6, 4), nullable=False)
    effective_from = Column(Date, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by_actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))


class ScoreRunInput(Base):
    """Append-only. One row per `score_runs.id`, capturing the exact
    `GradingInput` (plus the bank rate applied) used for that run.
    Structured columns, not JSONB, per the ledger pattern (CLAUDE.md) --
    a mapping that can be re-hydrated into a `GradingInput` and re-passed
    to `grade()` for an exact replay.

    Enforced append-only at the DB level (`trg_score_run_inputs_append_only`,
    reusing `ledger_immutability_guard()`), matching `state_transition`
    (T6) and the ledger tables themselves."""

    __tablename__ = "score_run_inputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    score_run_id = Column(
        UUID(as_uuid=True), ForeignKey("score_runs.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    company_code = Column(Text, nullable=False)
    industry = Column(Text, nullable=False)
    company_size = Column(Text, nullable=False)
    loan_size_vnd = Column(Numeric(20, 0), nullable=False)
    duration_months = Column(Integer, nullable=False)
    operating_months = Column(Integer, nullable=False)

    # 24 months, m1..m24, in order. Postgres arrays permit NULL elements,
    # which is how a caller represents a missing month (R8, INSUFFICIENT_DATA).
    monthly_revenue_vnd = Column(ARRAY(Numeric(20, 0)), nullable=False)

    cogs_y1_vnd = Column(Numeric(20, 0), nullable=False)
    fixed_cost_y1_vnd = Column(Numeric(20, 0), nullable=False)
    variable_cost_excl_cogs_y1_vnd = Column(Numeric(20, 0), nullable=False)

    conc_top1_pct = Column(Float)
    conc_top3_pct = Column(Float)
    crr = Column(Float)
    rri = Column(Float)
    tcp = Column(Float)

    sector_cagr_pct = Column(Float, nullable=False)
    sector_reference_version = Column(Text)  # null if not sourced from the resolver

    ai_score_regulatory = Column(Float)
    ai_score_input_cost_vol = Column(Float)
    ai_score_cyclicality = Column(Float)
    ai_score_competitor = Column(Float)
    ai_score_macro = Column(Float)
    ai_score_uncontrollable = Column(Float)
    ai_score_founder = Column(Float)

    owner_withdrawal = Column(Float)
    cic_score = Column(Integer)
    kyc_aml_passed = Column(Boolean)
    fraud_flags = Column(ARRAY(Text), nullable=False, server_default="{}")

    bank_rate_pct = Column(Numeric(6, 4), nullable=False)
    bank_rate_effective_from = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    score_run = relationship("ScoreRun", backref="inputs")
