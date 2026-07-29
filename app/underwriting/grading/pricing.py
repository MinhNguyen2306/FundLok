"""Interest rate, target payment, repayment, daily rate.

Spec: docs/specs/underwriting/grading-engine-core.md, R10.

    interest_rate_pct     = min(20.0, bank_rate_pct + (20 - bank_rate_pct) * (100 - final_grade) / 100)
    target_payment_vnd    = loan_size * (1 + interest_rate_pct/100 * duration_months/12)
    target_daily_vnd      = target_payment_vnd / (duration_months * 21)
    avg_daily_revenue_vnd = revenue_y1 / 252
    daily_repayment_rate  = target_daily_vnd / avg_daily_revenue_vnd

The golden set CANNOT validate this section -- the workbook's pricing columns
come from a stale, different dataset than its grade columns (9,938 of 10,000
rows disagree on loan size and term; see deviations register D13). This is
tested against the closed-form arithmetic above and the worked example in
spec section 8, not against the fixture.

Money boundary (R4): `loan_size_vnd`, `target_payment_vnd`, `target_daily_vnd`
and `avg_daily_revenue_vnd` are `Decimal`. `interest_rate_pct` and
`daily_repayment_rate` are `float` -- they derive from `final_grade`, which is
float, and R5 requires full precision through to the rate (rounding the grade
first before computing the rate misprices a 3bn loan by hundreds of thousands
of VND).
"""
from __future__ import annotations

from decimal import Decimal
from typing import NamedTuple

from .params import ParamSet

__all__ = ["PricingResult", "price"]


class PricingResult(NamedTuple):
    interest_rate_pct: float
    target_payment_vnd: Decimal
    target_daily_vnd: Decimal
    avg_daily_revenue_vnd: Decimal
    daily_repayment_rate: float


def price(
    *,
    final_grade: float,
    bank_rate_pct: float,
    loan_size_vnd: Decimal,
    duration_months: int,
    revenue_y1_vnd: Decimal,
    params: ParamSet,
) -> PricingResult:
    rate_cap_pct = params.pricing["rate_cap_pct"]

    if bank_rate_pct >= rate_cap_pct:
        # D17: the min() below is unreachable while bank_rate_pct < cap. If
        # bank_rate_pct is ever configured >= the cap, the formula would
        # price every borrower at exactly the cap -- a config error, not a
        # valid state, so this raises rather than silently doing that.
        raise ValueError(
            f"bank_rate_pct ({bank_rate_pct}) >= rate cap ({rate_cap_pct}); "
            "refusing to price every borrower at the cap -- see R10 / "
            "deviations register D17"
        )

    interest_rate_pct = min(
        rate_cap_pct,
        bank_rate_pct + (rate_cap_pct - bank_rate_pct) * (100.0 - final_grade) / 100.0,
    )

    working_days_per_month = Decimal(str(params.repayment["working_days_per_month"]))
    working_days_per_year = Decimal(str(params.repayment["working_days_per_year"]))

    # Convert once, at the boundary (R4) -- from here down everything stays
    # Decimal.
    rate_fraction = Decimal(str(interest_rate_pct)) / Decimal("100")
    duration_dec = Decimal(duration_months)

    target_payment_vnd = loan_size_vnd * (Decimal("1") + rate_fraction * duration_dec / Decimal("12"))
    target_daily_vnd = target_payment_vnd / (duration_dec * working_days_per_month)
    avg_daily_revenue_vnd = revenue_y1_vnd / working_days_per_year
    daily_repayment_rate = float(target_daily_vnd / avg_daily_revenue_vnd)

    return PricingResult(
        interest_rate_pct=interest_rate_pct,
        target_payment_vnd=target_payment_vnd,
        target_daily_vnd=target_daily_vnd,
        avg_daily_revenue_vnd=avg_daily_revenue_vnd,
        daily_repayment_rate=daily_repayment_rate,
    )
