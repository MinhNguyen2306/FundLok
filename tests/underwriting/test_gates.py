"""8 knockout gates + decision resolution.

Spec: docs/specs/underwriting/grading-engine-core.md, R9, section 8.
"""
from decimal import Decimal

from app.underwriting.grading import grade, load_params

from .conftest import GRADING_PARAMS_PATH, make_valid_input


def test_hard_gate_produces_reject():
    inputs = make_valid_input(kyc_aml_passed=False)
    result = grade(inputs, load_params())
    assert result.decision == "REJECT"


def test_soft_gate_produces_review():
    inputs = make_valid_input(operating_months=10)  # < 24: gate 1 (soft)
    result = grade(inputs, load_params())
    assert result.decision == "REVIEW"
    assert not any(g.severity == "hard" for g in result.fired_gates)
    assert any(g.severity == "soft" for g in result.fired_gates)


def test_no_gate_produces_approved():
    # Sized so daily_repayment_rate stays comfortably under the 0.30 gate,
    # with a long operating history relative to the term.
    inputs = make_valid_input(
        loan_size_vnd=Decimal("500000000"),
        duration_months=12,
        operating_months=48,
        monthly_revenue=tuple(Decimal("300000000") for _ in range(24)),
        cogs_y1=Decimal("1500000000"),
        fixed_cost_y1=Decimal("500000000"),
        variable_cost_excl_cogs_y1=Decimal("500000000"),
    )
    result = grade(inputs, load_params())
    assert result.fired_gates == ()
    assert result.decision == "APPROVED"


def test_hard_gate_beats_soft_gate():
    inputs = make_valid_input(kyc_aml_passed=False, operating_months=10)
    result = grade(inputs, load_params())
    fired_keys = {g.key for g in result.fired_gates}
    assert "kyc_aml" in fired_keys  # hard
    assert "operating_history" in fired_keys  # soft, also fired
    assert result.decision == "REJECT"  # hard wins


def test_gate_3_disabled_by_default_and_config_switchable(params, tmp_path):
    gate3 = next(g for g in params.gates if g.key == "low_factor_count")
    assert gate3.enabled is False

    original_text = GRADING_PARAMS_PATH.read_text()
    switched_text = original_text.replace(
        "enabled: false, threshold: null}",
        "enabled: true, threshold: 3}",
    )
    assert switched_text != original_text  # the replace actually matched

    switched_yaml = tmp_path / "grading_params_v1.yaml"
    switched_yaml.write_text(switched_text)

    switched_params = load_params(path=switched_yaml)
    switched_gate3 = next(g for g in switched_params.gates if g.key == "low_factor_count")
    assert switched_gate3.enabled is True
    assert switched_gate3.threshold == 3

    # And it now actually fires -- no code change, only the params file.
    inputs = make_valid_input()
    result = grade(inputs, switched_params)
    below_50 = sum(1 for s in result.factor_scores.values() if s is not None and s < 50)
    fired_keys = {g.key for g in result.fired_gates}
    if below_50 >= 3:
        assert "low_factor_count" in fired_keys
    else:
        assert "low_factor_count" not in fired_keys


def test_gate_7_disabled_by_default_and_config_switchable(params, tmp_path):
    gate7 = next(g for g in params.gates if g.key == "cic_floor")
    assert gate7.enabled is False

    original_text = GRADING_PARAMS_PATH.read_text()
    switched_text = original_text.replace(
        'rule: "cic_score <= 500", enabled: false}',
        'rule: "cic_score <= 500", enabled: true}',
    )
    assert switched_text != original_text

    switched_yaml = tmp_path / "grading_params_v1.yaml"
    switched_yaml.write_text(switched_text)

    switched_params = load_params(path=switched_yaml)
    switched_gate7 = next(g for g in switched_params.gates if g.key == "cic_floor")
    assert switched_gate7.enabled is True

    inputs = make_valid_input(cic_score=400)  # <= 500
    result = grade(inputs, switched_params)
    assert any(g.key == "cic_floor" for g in result.fired_gates)
    assert result.decision == "REJECT"

    # With gate 7 disabled (the shipped default), the same low CIC score
    # does not hard-reject on that basis.
    inputs_default_params = grade(inputs, params)
    assert not any(g.key == "cic_floor" for g in inputs_default_params.fired_gates)


def test_gate_2_uses_term_over_operating_history_not_inverse():
    # duration_months=3, operating_months=100: correct rule
    # (3 > 0.25*100 == 25) is False -- a long-established business taking a
    # short-term loan should NOT trip this gate. The inverted rule
    # (operating_months > 0.25*duration_months, i.e. 100 > 0.75) would fire
    # here, so this discriminates between the two.
    inputs = make_valid_input(duration_months=3, operating_months=100)
    result = grade(inputs, load_params())
    fired_keys = {g.key for g in result.fired_gates}
    assert "history_vs_term" not in fired_keys


def test_excluded_industry_rejects():
    inputs = make_valid_input(industry="tobacco")
    result = grade(inputs, load_params())
    assert result.decision == "REJECT"
    assert any(g.key == "excluded_industry" for g in result.fired_gates)


def test_fraud_flag_rejects():
    inputs = make_valid_input(fraud_flags=("velocity_abuse",))
    result = grade(inputs, load_params())
    assert result.decision == "REJECT"
    assert any(g.key == "kyc_aml" for g in result.fired_gates)


def test_fired_gates_are_reported_with_ids():
    inputs = make_valid_input(kyc_aml_passed=False)
    result = grade(inputs, load_params())
    kyc_gate = next(g for g in result.fired_gates if g.key == "kyc_aml")
    assert kyc_gate.id == 6
    assert kyc_gate.severity == "hard"
