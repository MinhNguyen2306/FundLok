"""Interest rate, target payment, repayment, daily rate.

Spec: docs/specs/underwriting/grading-engine-core.md, R10, section 8.

The golden set cannot validate this section (deviations register D13 -- the
workbook's pricing columns come from a stale, different dataset than its
grade columns). These test the closed-form arithmetic directly, and the
worked example from spec section 8.
"""
from decimal import Decimal

import pytest

from app.underwriting.grading import pricing


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


def test_daily_repayment_rate_uses_21_and_252_day_conventions(params):
    result = pricing.price(
        final_grade=50.0,
        bank_rate_pct=12.0,
        loan_size_vnd=Decimal("1000000000"),
        duration_months=6,
        revenue_y1_vnd=Decimal("2520000000"),
        params=params,
    )
    assert result.avg_daily_revenue_vnd == Decimal("2520000000") / Decimal("252")

    expected_target_daily = result.target_payment_vnd / (Decimal(6) * Decimal(21))
    assert result.target_daily_vnd == expected_target_daily

    expected_rate = float(result.target_daily_vnd / result.avg_daily_revenue_vnd)
    assert result.daily_repayment_rate == pytest.approx(expected_rate, rel=1e-12)


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
