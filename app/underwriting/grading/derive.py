"""Ingested fields -> derived raw metrics.

Spec: docs/specs/underwriting/grading-engine-core.md, R6. Three of these are
counter-intuitive; all are confirmed against all 10,000 rows of the golden
set, so if a value here looks wrong, re-read R6 before "fixing" it.

Money boundary (R4): `monthly_revenue`, `cogs_y1`, `fixed_cost_y1` and
`variable_cost_excl_cogs_y1` arrive as `Decimal`. Every derived metric here is
a `float` -- the workbook computed in IEEE double precision and matching it to
1e-7 requires float, not `Decimal`. The one exception is
`revenue_y1_decimal()`, kept in `Decimal` for `pricing.py`'s
`avg_daily_revenue_vnd`, which is a money field.
"""
from __future__ import annotations

import statistics
from decimal import Decimal
from typing import Mapping, Optional, Sequence

from .types import GradingInput

__all__ = [
    "revenue_y1_decimal",
    "total_cost_decimal",
    "min_trailing_twelve_decimal",
    "compute_derived",
]


def revenue_y1_decimal(monthly_revenue: Sequence[Decimal]) -> Decimal:
    """`revenue_y1 = sum(m13..m24)` -- the most recent 12 months. `m1..m12`
    is the prior year and is only used by revenue trend (R6 #1, #7)."""
    trailing = monthly_revenue[12:24]
    return sum(trailing, Decimal("0"))


def total_cost_decimal(inputs: GradingInput) -> Decimal:
    """COGS is its own field -- it is NOT folded into variable cost (R6 #2)."""
    return inputs.cogs_y1 + inputs.fixed_cost_y1 + inputs.variable_cost_excl_cogs_y1


def min_trailing_twelve_decimal(monthly_revenue: Sequence[Decimal]) -> Decimal:
    return min(monthly_revenue[12:24])


def compute_derived(inputs: GradingInput) -> Mapping[str, Optional[float]]:
    """Compute all derived metrics as float, per R4/R6.

    Callers must guard the R8 zero/None conditions (fewer than 24 months, any
    month `None`, revenue_y1 == 0, total_cost == 0, min(m13..m24) == 0)
    *before* calling this -- those produce `INSUFFICIENT_DATA`, a return
    value, not an exception. This function assumes that guard already passed
    and will raise `ZeroDivisionError` if it didn't.

    `profit <= 0` is different: the workbook has no rule for it, and on the
    SCSR curve a negative ratio scores ~100 -- rewarding a loss-making SME.
    Per spec section 7 (Error Cases) / deviations register D21, this raises
    `ValueError` and is *not* converted into a decision state; it propagates
    to the caller.
    """
    monthly = inputs.monthly_revenue
    trailing = [float(v) for v in monthly[12:24]]
    leading = [float(v) for v in monthly[0:12]]

    revenue_y1 = float(revenue_y1_decimal(monthly))
    avg_monthly_revenue = revenue_y1 / 12.0

    total_cost = float(total_cost_decimal(inputs))
    avg_monthly_cost = total_cost / 12.0

    profit = revenue_y1 - total_cost

    cogs = float(inputs.cogs_y1)
    variable_excl_cogs = float(inputs.variable_cost_excl_cogs_y1)

    gross_margin_pct = (revenue_y1 - cogs) / revenue_y1 * 100.0
    contribution_margin_pct = (revenue_y1 - variable_excl_cogs - cogs) / revenue_y1 * 100.0
    operating_margin_pct = (revenue_y1 - total_cost) / revenue_y1 * 100.0
    cost_flexibility_pct = (cogs + variable_excl_cogs) / total_cost * 100.0

    duration_months = float(inputs.duration_months)
    loan_size = float(inputs.loan_size_vnd)

    # "Total-duration revenue" is avg_monthly_revenue x duration_months -- an
    # average projected over the term, NOT the trailing `duration` actual
    # months (R6 #4). Likewise for SCSR (R6 #5).
    loan_revenue_ratio = loan_size / (avg_monthly_revenue * duration_months)

    if profit <= 0:
        raise ValueError(
            "profit <= 0: scsr_ratio would be negative/undefined and the "
            "SCSR curve scores a negative ratio ~100, rewarding a "
            "loss-making SME. Refusing to score this application -- see "
            "spec section 7 / deviations register D21."
        )
    scsr_ratio = loan_size / ((avg_monthly_revenue - avg_monthly_cost) * duration_months)

    # Population standard deviation (STDEV.P), NOT sample -- over m13..m24
    # only (R6 #6).
    revenue_volatility_cv = statistics.pstdev(trailing) / statistics.mean(trailing)

    # Mean of ten overlapping 3-month windows, each vs. the same window
    # twelve months earlier (R6 #7). `trailing[0] == m13`, `leading[0] ==
    # m1`, so window k compares trailing[k:k+3] (m[13+k..15+k]) against
    # leading[k:k+3] (m[1+k..3+k]). This is NOT a mean of twelve monthly
    # year-on-year ratios.
    windows = []
    for k in range(10):
        recent = sum(trailing[k:k + 3])
        prior = sum(leading[k:k + 3])
        windows.append((recent - prior) / prior)
    revenue_trend_decimal = statistics.mean(windows)

    seasonality_ratio = max(trailing) / min(trailing)

    rti: Optional[float] = None
    if inputs.crr is not None and inputs.rri is not None and inputs.tcp is not None:
        # 0.5*CRR + 0.3*RRI + 0.2*TCP, all on a 0-100 scale (R6 #9). The
        # scoring step (factors.py) divides this by 100 before the sigmoid.
        rti = 0.5 * inputs.crr + 0.3 * inputs.rri + 0.2 * inputs.tcp

    return {
        "revenue_y1": revenue_y1,
        "avg_monthly_revenue": avg_monthly_revenue,
        "total_cost": total_cost,
        "avg_monthly_cost": avg_monthly_cost,
        "profit": profit,
        "gross_margin_pct": gross_margin_pct,
        "contribution_margin_pct": contribution_margin_pct,
        "operating_margin_pct": operating_margin_pct,
        "cost_flexibility_pct": cost_flexibility_pct,
        "loan_revenue_ratio": loan_revenue_ratio,
        "scsr_ratio": scsr_ratio,
        "revenue_volatility_cv": revenue_volatility_cv,
        "revenue_trend_decimal": revenue_trend_decimal,
        "seasonality_ratio": seasonality_ratio,
        "rti": rti,
    }
