"""Request/response schemas for `app/underwriting/router.py`.

`ScoreRunOut`'s shape follows spec §5.1 (T0e, resolved) exactly: money as
strings of integer VND, `grade` split into full-precision `value` and
2dp `display`, `pricing`/`grade.value` null (never 0/0.0) when the
decision is INSUFFICIENT_DATA or AI_PENDING, and every response carrying
a grade or price also carries the `versions` block.
"""
from datetime import date
from decimal import Decimal
from typing import Literal, Mapping, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel, Field


class ScoreRunCreate(BaseModel):
    """The real, load-bearing request shape for `POST /underwriting/score-runs`.

    This is intentionally minimal -- it is NOT "production callers
    assembling a GradingInput" (an earlier design in this handoff put ~20
    mandatory grading-input fields directly on this request; that was
    reverted because the shared test fixture `run_and_lock_score` in the
    root `conftest.py`, used throughout `open_listing`, `funded_contract`,
    `test_document_approval.py` and `test_loan_application_state.py`,
    posts exactly `{application_id, mode}` to this endpoint, and that is
    also the real, already-shipped API contract -- not something this
    handoff is free to redesign).

    The SME's financial data lives on `LoanApplicationFinancials`
    (mutable, upserted separately via
    `PUT /underwriting/applications/{application_id}/financials`) and is
    read by `start_score_run()` at scoring time, by `application_id`. An
    application with no financials row yet still starts a score run --
    it resolves to `INSUFFICIENT_DATA`, per R8, rather than erroring.
    """

    application_id: UUID
    mode: str | None = None


class ApplicationFinancialsCreate(BaseModel):
    """Body for `PUT /underwriting/applications/{application_id}/financials`
    -- upserts `LoanApplicationFinancials`. Mirrors that model's writable
    columns exactly (see `app/lending/models.py`).

    `industry`, `company_size`, `duration_months` and `operating_months`
    are required: `grade()`'s `_validate_inputs` checks them regardless of
    data sufficiency (allowed duration set, recognised industry), so they
    are config/input parameters, not missing-data states. Everything else
    is optional -- absence there is exactly what produces
    INSUFFICIENT_DATA (R8), not a validation error.
    """

    industry: str
    company_size: Literal["micro", "small", "medium"]
    duration_months: int
    operating_months: int

    # Exactly 24 values, m1..m24, in order, when supplied. `None` entries
    # (or omitting the field) are how a missing month is represented (R8).
    monthly_revenue_vnd: Optional[Sequence[Optional[int]]] = Field(default=None, min_length=24, max_length=24)

    cogs_y1_vnd: Optional[int] = None
    fixed_cost_y1_vnd: Optional[int] = None
    variable_cost_excl_cogs_y1_vnd: Optional[int] = None

    conc_top1_pct: Optional[float] = None
    conc_top3_pct: Optional[float] = None
    crr: Optional[float] = None
    rri: Optional[float] = None
    tcp: Optional[float] = None

    # Overrides for the sector-reference-resolved values (R6). Normally omitted.
    sector_cagr_pct_override: Optional[float] = None
    ai_score_regulatory_override: Optional[float] = None
    ai_score_input_cost_vol_override: Optional[float] = None
    ai_score_cyclicality_override: Optional[float] = None
    ai_score_competitor_override: Optional[float] = None
    ai_score_macro_override: Optional[float] = None
    ai_score_uncontrollable_override: Optional[float] = None
    ai_score_founder_override: Optional[float] = None

    owner_withdrawal: Optional[float] = None
    cic_score: Optional[int] = None
    kyc_aml_passed: Optional[bool] = None
    fraud_flags: Sequence[str] = ()


class ApplicationFinancialsOut(BaseModel):
    id: UUID
    application_id: UUID

    industry: str
    company_size: str
    duration_months: int
    operating_months: int

    monthly_revenue_vnd: Optional[Sequence[Optional[int]]]

    cogs_y1_vnd: Optional[int]
    fixed_cost_y1_vnd: Optional[int]
    variable_cost_excl_cogs_y1_vnd: Optional[int]

    conc_top1_pct: Optional[float]
    conc_top3_pct: Optional[float]
    crr: Optional[float]
    rri: Optional[float]
    tcp: Optional[float]

    sector_cagr_pct_override: Optional[float]
    ai_score_regulatory_override: Optional[float]
    ai_score_input_cost_vol_override: Optional[float]
    ai_score_cyclicality_override: Optional[float]
    ai_score_competitor_override: Optional[float]
    ai_score_macro_override: Optional[float]
    ai_score_uncontrollable_override: Optional[float]
    ai_score_founder_override: Optional[float]

    owner_withdrawal: Optional[float]
    cic_score: Optional[int]
    kyc_aml_passed: Optional[bool]
    fraud_flags: Sequence[str]

    model_config = {"from_attributes": True}


class VersionsOut(BaseModel):
    engine: str
    params: str
    sector_reference: Optional[str]
    bank_rate_pct: float
    bank_rate_effective_from: date


class GradeOut(BaseModel):
    value: Optional[float]  # full precision
    display: Optional[float]  # 2dp, for UI


class PricingOut(BaseModel):
    interest_rate_pct: float
    target_payment_vnd: str
    target_daily_vnd: str
    avg_daily_revenue_vnd: str
    daily_repayment_rate: float


class GateOut(BaseModel):
    id: int
    key: str
    severity: str


class ScoreRunOut(BaseModel):
    id: UUID
    application_id: UUID
    status: str
    created_at: Optional[str]
    locked_at: Optional[str]

    decision: Literal["APPROVED", "REVIEW", "REJECT", "INSUFFICIENT_DATA", "AI_PENDING"]
    grade: GradeOut
    pricing: Optional[PricingOut]
    premiums: Mapping[str, float]
    factor_scores: Mapping[str, Optional[float]]
    fired_gates: Sequence[GateOut]
    versions: VersionsOut


class ScoreRunApproveOut(BaseModel):
    id: UUID
    locked_at: str | None
    status: str


class SupportedIndustriesOut(BaseModel):
    """T3 / Issue 17: served, not transcribed -- Phat's dropdown is
    generated from this response, not a hardcoded frontend copy of
    `grading_params_v1.yaml`."""

    supported_industries: Sequence[str]
    excluded_industries: Sequence[str]
    params_version: str


class BankRateConfigCreate(BaseModel):
    """T0b: setting a new board-approved rate, effective from a future
    (or today's) date. Past rows are never edited -- a rate change is a
    new row."""

    rate_pct: Decimal
    effective_from: date


class BankRateConfigOut(BaseModel):
    id: UUID
    rate_pct: Decimal
    effective_from: date

    model_config = {"from_attributes": True}
