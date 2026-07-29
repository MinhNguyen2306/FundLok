"""Full precision to the edge -- round only for display.

Spec: docs/specs/underwriting/grading-engine-core.md, R4, R5, section 8.
"""
from decimal import Decimal

import pytest

from app.underwriting.grading import grade

from .conftest import make_valid_input, row_to_grading_input


def test_final_grade_is_not_rounded(params, golden_row):
    inputs = row_to_grading_input(golden_row)
    result = grade(inputs, params)

    assert result.final_grade == pytest.approx(70.98376463, abs=1e-6)
    assert result.final_grade != 71
    assert round(result.final_grade) != result.final_grade


def test_interest_rate_derives_from_unrounded_grade(params, golden_row):
    inputs = row_to_grading_input(golden_row)
    result = grade(inputs, params)

    # bank_rate_pct for this row is 12.0 (see spec section 8 worked example).
    assert inputs.bank_rate_pct == pytest.approx(12.0)
    assert result.interest_rate_pct == pytest.approx(14.32129883, abs=1e-4)

    # Using a grade of 71.0 (rounded) instead of the true 70.98376463 gives
    # 14.32 -- close enough to look right, wrong enough to matter on a 3bn
    # loan (R5). Confirm the engine's rate is NOT that rounded-grade value.
    rate_from_rounded_grade = 12.0 + 8.0 * (100.0 - 71.0) / 100.0
    assert result.interest_rate_pct != pytest.approx(rate_from_rounded_grade, abs=1e-6)


def test_money_fields_are_decimal_not_float(params):
    inputs = make_valid_input()
    result = grade(inputs, params)

    assert isinstance(result.target_payment_vnd, Decimal)
    assert isinstance(result.target_daily_vnd, Decimal)
    assert isinstance(result.avg_daily_revenue_vnd, Decimal)
    assert isinstance(inputs.loan_size_vnd, Decimal)

    assert isinstance(result.final_grade, float)
    assert isinstance(result.interest_rate_pct, float)
    assert isinstance(result.daily_repayment_rate, float)
