"""Frozen input/output types for the grading core.

Spec: docs/specs/underwriting/grading-engine-core.md, section 3.

These are plain dataclasses with no behaviour. Per R1 (spec section 6), this
package imports nothing from `app/` -- these types stand alone rather than
reusing Pydantic schemas or ORM models from elsewhere in the codebase.

Deviation from the spec's typed pseudocode: `final_grade`, `interest_rate_pct`,
`target_payment_vnd`, `target_daily_vnd`, `avg_daily_revenue_vnd` and
`daily_repayment_rate` are typed `Optional` here even though section 3 lists
them as bare `float`/`Decimal`. When `decision == "INSUFFICIENT_DATA"`, R8 is
explicit that "no scoring attempted" -- there is no grade or price to report,
and reporting `0.0` would look exactly like the low score R8 says we must
never produce. `None` is the only honest value in that branch.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal, Mapping, Optional, Tuple

CompanySize = Literal["micro", "small", "medium"]

Decision = Literal["APPROVED", "REVIEW", "REJECT", "INSUFFICIENT_DATA", "AI_PENDING"]

GateSeverity = Literal["hard", "soft"]


@dataclass(frozen=True)
class GradingInput:
    """Already-normalised application data. Document ingest/parsing and AI
    grading happen upstream of this type -- see spec section 2 (Out of Scope).
    """

    company_code: str
    industry: str
    company_size: CompanySize
    loan_size_vnd: Decimal
    duration_months: int
    operating_months: int

    # EXACTLY 24 values, m1 .. m24, in order, when data is sufficient. A
    # shorter tuple, or any `None` entry, is a valid *value* here (it is how
    # callers represent missing months) and is handled by R8 --
    # `INSUFFICIENT_DATA`, not a crash.
    monthly_revenue: Tuple[Optional[Decimal], ...]

    cogs_y1: Decimal
    fixed_cost_y1: Decimal
    variable_cost_excl_cogs_y1: Decimal

    conc_top1_pct: Optional[float]
    conc_top3_pct: Optional[float]
    crr: Optional[float]
    rri: Optional[float]
    tcp: Optional[float]

    sector_cagr_pct: float

    # Keys: regulatory, input_cost_vol, cyclicality, competitor, macro,
    # uncontrollable, founder -- each 0-100. Missing keys mean AI_PENDING
    # (R3, R8), never a computed value.
    ai_scores: Mapping[str, float]

    owner_withdrawal: Optional[float]
    cic_score: Optional[int]
    kyc_aml_passed: Optional[bool]
    fraud_flags: Tuple[str, ...]

    bank_rate_pct: float = 12.0


@dataclass(frozen=True)
class GateResult:
    """One fired gate. `fired_gates` on `GradingResult` only ever contains
    gates that actually fired -- there is no `fired=False` entry for a gate
    that didn't."""

    id: int
    key: str
    severity: GateSeverity


@dataclass(frozen=True)
class GradingResult:
    engine_version: str
    params_version: str

    derived: Mapping[str, float]
    factor_scores: Mapping[str, Optional[float]]
    premiums: Mapping[str, float]

    final_grade: Optional[float]
    interest_rate_pct: Optional[float]
    target_payment_vnd: Optional[Decimal]
    target_daily_vnd: Optional[Decimal]
    avg_daily_revenue_vnd: Optional[Decimal]
    daily_repayment_rate: Optional[float]

    fired_gates: Tuple[GateResult, ...]
    decision: Decision
