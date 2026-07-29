"""Missing data produces a state, never a low score.

Spec: docs/specs/underwriting/grading-engine-core.md, R8, section 8.
"""
from decimal import Decimal

import pytest

from app.underwriting.grading import grade, load_params

from .conftest import make_valid_input


def test_insufficient_data_when_fewer_than_24_months():
    inputs = make_valid_input(monthly_revenue=tuple(Decimal("100000000") for _ in range(20)))
    result = grade(inputs, load_params())
    assert result.decision == "INSUFFICIENT_DATA"


def test_insufficient_data_when_revenue_zero():
    inputs = make_valid_input(monthly_revenue=tuple(Decimal("0") for _ in range(24)))
    result = grade(inputs, load_params())
    assert result.decision == "INSUFFICIENT_DATA"


def test_insufficient_data_is_not_a_low_score():
    inputs = make_valid_input(cic_score=None)
    result = grade(inputs, load_params())

    assert result.decision == "INSUFFICIENT_DATA"
    assert all(score is None for score in result.factor_scores.values())
    assert result.final_grade is None
    assert result.premiums == {}

    # And, separately, kyc_aml_passed being None (rather than False) also
    # short-circuits to INSUFFICIENT_DATA, not a gate-driven REJECT.
    inputs_kyc_none = make_valid_input(kyc_aml_passed=None)
    result_kyc_none = grade(inputs_kyc_none, load_params())
    assert result_kyc_none.decision == "INSUFFICIENT_DATA"


def test_ai_pending_when_ai_score_missing():
    ai_scores = {
        "regulatory": 60.0,
        "input_cost_vol": 60.0,
        "cyclicality": 60.0,
        "competitor": 60.0,
        "macro": 60.0,
        "uncontrollable": 60.0,
        # founder deliberately absent
    }
    inputs = make_valid_input(ai_scores=ai_scores)
    result = grade(inputs, load_params())
    assert result.decision == "AI_PENDING"
    assert result.factor_scores["founder"] is None


def test_ai_pending_still_returns_deterministic_premiums():
    ai_scores = {
        "regulatory": 60.0,
        "input_cost_vol": 60.0,
        "cyclicality": 60.0,
        "competitor": 60.0,
        "macro": 60.0,
        "uncontrollable": 60.0,
    }
    inputs = make_valid_input(ai_scores=ai_scores)
    result = grade(inputs, load_params())

    assert result.decision == "AI_PENDING"
    assert result.final_grade is not None
    assert result.premiums["bcq"] > 0.0
    assert result.premiums["rsg"] > 0.0
    assert result.premiums["behavioral"] > 0.0
    # Sector is computed over the six present AI factors + sector_growth.
    assert result.premiums["sector"] > 0.0


def test_profit_not_positive_raises():
    inputs = make_valid_input(
        cogs_y1=Decimal("2000000000"),
        fixed_cost_y1=Decimal("500000000"),
        variable_cost_excl_cogs_y1=Decimal("100000000"),
    )
    with pytest.raises(ValueError):
        grade(inputs, load_params())
