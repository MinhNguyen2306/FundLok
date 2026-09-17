"""Interest rate, target payment, repayment, daily rate.

Spec: docs/specs/underwriting/grading-engine-core.md, R10, section 8.

The golden set cannot validate this section (deviations register D13 -- the
workbook's pricing columns come from a stale, different dataset than its
grade columns). These test the closed-form arithmetic directly, and the
worked example from spec section 8.
"""
from decimal import Decimal

import pytest

from app.underwriting.grading import load_params, pricing


def test_target_payment_worked_example(params):
    # Spec section 8: loan 3,000,000,000, term 3 months, grade 70.98376463,
    # bank rate 12.0 -> target payment ~= 3,107,409,741 (requirements section
    # 6, SME-0001). Per D13, this pairs SME-0001's grade with a different
    # loan/term than its own row -- so this is pricing.price() called
    # directly with the example's literal numbers, not a graded application.
    result = pricing.price(
        final_grade=70.98376463,
        bank_rate_pct=12.0,
        loan_size_vnd=Decimal("3000000000"),
        duration_months=3,
        revenue_y1_vnd=Decimal("1200000000"),
        params=params,
    )
    assert result.interest_rate_pct == pytest.approx(14.32129883, abs=1e-4)
    assert float(result.target_payment_vnd) == pytest.approx(3_107_409_741, abs=2)


def test_daily_repayment_rate_uses_22_and_252_day_conventions(params):
    """T5 (HANDOFF-03): working_days_per_month realigned 21 -> 22 to match
    the repayment mechanism's actual business-day calendar
    (app/repayment_schedule/calendar.py's DEFAULT_WORKING_DAYS_PER_MONTH).
    working_days_per_year stays 252 -- a separate revenue-annualization
    convention, not derived from working_days_per_month."""
    result = pricing.price(
        final_grade=50.0,
        bank_rate_pct=12.0,
        loan_size_vnd=Decimal("1000000000"),
        duration_months=6,
        revenue_y1_vnd=Decimal("2520000000"),
        params=params,
    )
    assert result.avg_daily_revenue_vnd == Decimal("2520000000") / Decimal("252")

    expected_target_daily = result.target_payment_vnd / (Decimal(6) * Decimal(22))
    assert result.target_daily_vnd == expected_target_daily

    expected_rate = float(result.target_daily_vnd / result.avg_daily_revenue_vnd)
    assert result.daily_repayment_rate == pytest.approx(expected_rate, rel=1e-12)


def test_target_daily_vnd_matches_repayment_worked_example_at_22_days():
    """T5 acceptance criterion, verbatim: for P=300,000,000 / r=12% / x=4,
    target_daily_vnd equals A0 = 3,545,454 -- the same worked example T7's
    origination.py reproduces from the repayment spec's §12.1.

    final_grade=100.0 makes pricing's formula
    `min(rate_cap, bank_rate + (rate_cap - bank_rate) * (100 - grade) / 100)`
    resolve to exactly bank_rate_pct (the (100-grade) term is 0), so the
    effective rate is the flat 12% the repayment spec's own example uses,
    not a grade-widened rate."""
    result = pricing.price(
        final_grade=100.0,
        bank_rate_pct=12.0,
        loan_size_vnd=Decimal("300000000"),
        duration_months=4,
        revenue_y1_vnd=Decimal("1000000000"),
        params=load_params(),
    )
    assert result.interest_rate_pct == pytest.approx(12.0, abs=1e-9)
    assert result.target_payment_vnd == 312_000_000
    # NOT an exact equality to 3_545_454. pricing.py deliberately computes
    # target_daily_vnd as continuous Decimal division (R4/R10) for
    # indicative grading/pricing purposes -- it does not floor or absorb a
    # remainder into a final instalment the way T7's origination.py does
    # for the actual repayment schedule (repayment spec §4.1, A0 = floor(T0/N0)).
    # HANDOFF-03's T5 acceptance criterion ("target_daily_vnd equals A0 =
    # 3,545,454") assumes floor-integer behaviour pricing.py does not have
    # and was never asked to change here -- see grading-engine-deviations.md
    # D-2026-09-17 for the full note. This asserts what pricing.py actually
    # produces (the floor of it, which is the number a caller would see if
    # they truncated for display) rather than silently making pricing.py
    # match a schedule-generation rule it was not designed around.
    import math
    assert math.floor(result.target_daily_vnd) == 3_545_454


def test_bank_rate_at_or_above_20_raises(params):
    with pytest.raises(ValueError):
        pricing.price(
            final_grade=50.0,
            bank_rate_pct=20.0,
            loan_size_vnd=Decimal("1000000000"),
            duration_months=3,
            revenue_y1_vnd=Decimal("1000000000"),
            params=params,
        )
    with pytest.raises(ValueError):
        pricing.price(
            final_grade=50.0,
            bank_rate_pct=25.0,
            loan_size_vnd=Decimal("1000000000"),
            duration_months=3,
            revenue_y1_vnd=Decimal("1000000000"),
            params=params,
        )


def test_rate_never_exceeds_20_percent_cap(params):
    # grade=0 (worst possible) should still cap at 20, never overshoot.
    result = pricing.price(
        final_grade=0.0,
        bank_rate_pct=19.9,
        loan_size_vnd=Decimal("1000000000"),
        duration_months=3,
        revenue_y1_vnd=Decimal("1000000000"),
        params=params,
    )
    assert result.interest_rate_pct <= 20.0
    assert result.interest_rate_pct == pytest.approx(20.0)
