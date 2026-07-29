"""4 group premiums + final grade.

Spec: docs/specs/underwriting/grading-engine-core.md, R7, section 8.
"""
import pytest

from app.underwriting.grading import rollup


def test_rsg_seasonality_weight_is_one_quarter_not_one_third(params):
    rsg_core = params.rollup["rsg"]["core"]
    assert rsg_core["seasonality"] == pytest.approx(0.25)
    assert rsg_core["revenue_volatility"] == pytest.approx(1 / 3)
    assert rsg_core["revenue_trend"] == pytest.approx(1 / 3)
    # Deliberate: the RSG core sums to 0.91666..., not 1.0 (R7).
    assert sum(rsg_core.values()) == pytest.approx(0.9166666666666666)
    assert sum(rsg_core.values()) != pytest.approx(1.0, abs=1e-9)


def test_behavioral_core_is_cic_at_full_weight(params):
    behavioral = params.rollup["behavioral"]
    assert dict(behavioral["core"]) == {"cic": 1.0}
    # Tax Discipline is absent entirely -- not a partial-weight member.
    assert "tax_discipline" not in behavioral["core"]
    assert "tax_discipline" not in behavioral["bonus"]


def test_tax_discipline_absent_from_rollup(params):
    factor_keys = {f.key for f in params.factors}
    assert "tax_discipline" not in factor_keys
    assert "data_reliability" not in factor_keys
    for group in params.rollup.values():
        assert "tax_discipline" not in group["core"]
        assert "tax_discipline" not in group["bonus"]


def test_bonus_factors_contribute_one_twentieth(params):
    any_bonus = False
    for group in params.rollup.values():
        for weight in group["bonus"].values():
            any_bonus = True
            assert weight == pytest.approx(0.05)  # score/20 == score * 0.05
    assert any_bonus


def test_none_bonus_contributes_zero():
    group_weights = {"core": {"a": 1.0}, "bonus": {"b": 0.05}}

    with_bonus = rollup.compute_group_premium(group_weights, {"a": 80.0, "b": 40.0})
    without_bonus = rollup.compute_group_premium(group_weights, {"a": 80.0, "b": None})

    assert with_bonus == pytest.approx(80.0 + 0.05 * 40.0)
    assert without_bonus == pytest.approx(80.0)  # None contributes exactly 0, not a penalty


def test_final_grade_weights_are_40_25_25_10(params):
    assert params.final_grade["bcq"] == pytest.approx(0.40)
    assert params.final_grade["rsg"] == pytest.approx(0.25)
    assert params.final_grade["sector"] == pytest.approx(0.25)
    assert params.final_grade["behavioral"] == pytest.approx(0.10)
    assert sum(params.final_grade.values()) == pytest.approx(1.0)
