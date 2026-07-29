"""Orchestrator: the only function callers need.

Spec: docs/specs/underwriting/grading-engine-core.md, section 4 / R8.

    from app.underwriting.grading import grade, load_params, GradingInput, GradingResult

    params = load_params()
    result: GradingResult = grade(inputs, params)

`grade()` is synchronous by design (R1) -- it is CPU-bound arithmetic with no
awaitable inside it. The async boundary belongs in `app/underwriting/service.py`
(spec 2), which awaits the DB and calls `grade()` synchronously. Do not make
this async.
"""
from __future__ import annotations

from decimal import Decimal
from types import MappingProxyType
from typing import Optional

from . import derive, factors, gates, pricing, rollup
from .params import ParamSet, load_params
from .types import GradingInput, GradingResult

__all__ = ["grade"]


def _validate_inputs(inputs: GradingInput, params: ParamSet) -> None:
    """Section 7 (Error Cases) validations that apply regardless of data
    sufficiency -- these are config/input errors, not missing-data states,
    so they raise `ValueError` rather than producing `INSUFFICIENT_DATA`."""
    if inputs.duration_months not in params.loan_constraints["allowed_durations_months"]:
        raise ValueError(
            f"duration_months {inputs.duration_months} not in allowed set "
            f"{params.loan_constraints['allowed_durations_months']}"
        )

    min_vnd = Decimal(str(params.loan_constraints["min_vnd"]))
    max_vnd = Decimal(str(params.loan_constraints["max_vnd"]))
    if not (min_vnd <= inputs.loan_size_vnd <= max_vnd):
        raise ValueError(f"loan_size_vnd {inputs.loan_size_vnd} outside [{min_vnd}, {max_vnd}]")

    # An excluded industry (gambling, alcohol, tobacco, weapons, defence) is
    # not in `supported_industries` either -- there's no sector scoring data
    # for it -- but it is still a *recognised* industry, not a typo/garbage
    # value. It must be allowed through validation so gate 5
    # (`excluded_industry`, hard) can reject it after grading runs, the same
    # way `kyc_aml` does. Only an industry in neither list is a genuine
    # input error.
    if inputs.industry not in params.supported_industries and inputs.industry not in params.excluded_industries:
        raise ValueError(f"industry {inputs.industry!r} not in supported_industries or excluded_industries")

    if inputs.bank_rate_pct >= params.pricing["rate_cap_pct"]:
        raise ValueError(f"bank_rate_pct {inputs.bank_rate_pct} >= rate cap {params.pricing['rate_cap_pct']}")


def _insufficient_data_result(params: ParamSet) -> GradingResult:
    """R8: "no scoring attempted" -- premiums/grade/derived are genuinely
    absent here, not zero. Reporting zeros would be exactly the "missing data
    reads as a low score" failure mode R8 exists to prevent."""
    return GradingResult(
        engine_version=params.engine_version,
        params_version=params.params_version,
        derived=MappingProxyType({}),
        factor_scores=MappingProxyType({factor.key: None for factor in params.factors}),
        premiums=MappingProxyType({}),
        final_grade=None,
        interest_rate_pct=None,
        target_payment_vnd=None,
        target_daily_vnd=None,
        avg_daily_revenue_vnd=None,
        daily_repayment_rate=None,
        fired_gates=(),
        decision="INSUFFICIENT_DATA",
    )


def _is_insufficient_data(inputs: GradingInput) -> bool:
    monthly = inputs.monthly_revenue
    if len(monthly) != 24 or any(v is None for v in monthly):
        return True
    if inputs.cic_score is None or inputs.kyc_aml_passed is None:
        return True

    revenue_y1 = derive.revenue_y1_decimal(monthly)
    total_cost = derive.total_cost_decimal(inputs)
    min_trailing = derive.min_trailing_twelve_decimal(monthly)
    return revenue_y1 == 0 or total_cost == 0 or min_trailing == 0


def grade(inputs: GradingInput, params: Optional[ParamSet] = None) -> GradingResult:
    if params is None:
        params = load_params()

    _validate_inputs(inputs, params)

    if _is_insufficient_data(inputs):
        return _insufficient_data_result(params)

    # Raises ValueError if profit <= 0 (R8/R10, deviations register D21) --
    # that propagates to the caller rather than becoming a decision state.
    derived = derive.compute_derived(inputs)

    factor_scores = factors.score_all_factors(params, inputs, derived)
    premiums, final_grade_value = rollup.compute_rollup(params, factor_scores)

    ai_pending = any(factor_scores[key] is None for key in factors.AI_SCORE_KEYS)

    revenue_y1_vnd = derive.revenue_y1_decimal(inputs.monthly_revenue)
    pricing_result = pricing.price(
        final_grade=final_grade_value,
        bank_rate_pct=inputs.bank_rate_pct,
        loan_size_vnd=inputs.loan_size_vnd,
        duration_months=inputs.duration_months,
        revenue_y1_vnd=revenue_y1_vnd,
        params=params,
    )

    fired_gates = gates.evaluate_gates(params, inputs, factor_scores, pricing_result.daily_repayment_rate)
    hard_fired = any(g.severity == "hard" for g in fired_gates)
    soft_fired = any(g.severity == "soft" for g in fired_gates)

    # Resolution order (R9 gives hard > soft > approved; AI_PENDING is
    # folded in here since a hard gate -- KYC/fraud/excluded industry -- is
    # an absolute block that should not be masked by "still waiting on AI
    # scores", while an ordinary review is superseded by "we can't finish
    # grading yet").
    if hard_fired:
        decision = "REJECT"
    elif ai_pending:
        decision = "AI_PENDING"
    elif soft_fired:
        decision = "REVIEW"
    else:
        decision = "APPROVED"

    return GradingResult(
        engine_version=params.engine_version,
        params_version=params.params_version,
        derived=MappingProxyType(dict(derived)),
        factor_scores=MappingProxyType(dict(factor_scores)),
        premiums=MappingProxyType(dict(premiums)),
        final_grade=final_grade_value,
        interest_rate_pct=pricing_result.interest_rate_pct,
        target_payment_vnd=pricing_result.target_payment_vnd,
        target_daily_vnd=pricing_result.target_daily_vnd,
        avg_daily_revenue_vnd=pricing_result.avg_daily_revenue_vnd,
        daily_repayment_rate=pricing_result.daily_repayment_rate,
        fired_gates=fired_gates,
        decision=decision,
    )
