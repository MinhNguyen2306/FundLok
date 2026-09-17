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
    """T3: "production callers assembling a GradingInput." This endpoint
    is admin-gated (`require_admin`), so the caller is an ops tool or
    internal review flow that has already collected/verified an SME's
    financials, AI scores, CIC result and KYC/AML outcome -- there is no
    document-ingest or AI-scoring pipeline in this handoff's scope (see
    grading-engine's own `types.py`: "Document ingest/parsing and AI
    grading happen upstream of this type"), so the caller supplies the
    already-normalised `GradingInput` fields directly.

    `industry`, `company_size` and the six sector AI-score keys plus
    `sector_cagr_pct` may be omitted -- `service.py` fills them in from
    `resolve_sector_inputs()` (T3's sector reference table) when omitted,
    per the sector-reference spec's intended usage. Pass them explicitly
    only to override the table (R6's "upgrade path" -- a future
    per-application LLM score for one of those six factors).
    """

    application_id: UUID
    mode: str | None = None

    company_code: str
    industry: str
    company_size: Literal["micro", "small", "medium"]
    loan_size_vnd: int
    duration_months: int
    operating_months: int

    # Exactly 24 values, m1..m24, in order. `None` entries are how a
    # caller represents a missing month (R8, INSUFFICIENT_DATA) -- not an
    # error.
    monthly_revenue_vnd: Sequence[Optional[int]] = Field(min_length=24, max_length=24)

    cogs_y1_vnd: int
    fixed_cost_y1_vnd: int
    variable_cost_excl_cogs_y1_vnd: int

    conc_top1_pct: Optional[float] = None
    conc_top3_pct: Optional[float] = None
    crr: Optional[float] = None
    rri: Optional[float] = None
    tcp: Optional[float] = None

    # Overrides for the sector-reference-resolved values (R6). Normally omitted.
    sector_cagr_pct: Optional[float] = None
    ai_scores: Optional[Mapping[str, float]] = None

    owner_withdrawal: Optional[float] = None
    cic_score: Optional[int] = None
    kyc_aml_passed: Optional[bool] = None
    fraud_flags: Sequence[str] = ()


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
