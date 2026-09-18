"""8 knockout gates + decision resolution.

Spec: docs/specs/underwriting/grading-engine-core.md, R9, section 8.
"""
from decimal import Decimal

from app.underwriting.grading import grade, load_params

from .conftest import GRADING_PARAMS_PATH, iter_golden_set_full, make_valid_input, row_to_grading_input


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


def test_gate_3_enabled_at_threshold_13_per_t0a(params):
    """T0a (Loc, 17 Sep 2026): gate 3 is now enabled at threshold: 13 --
    was disabled pending a business decision on where to set it (98.4%/
    95.2% fire rates at the previously-considered >=3/>=4 thresholds were
    unusable). This is config, not code: the gate's own rule
    (`count(factor_scores < 50) >= threshold`) and `evaluate_gates`'s
    `if not gate.enabled: continue` check are both unchanged."""
    gate3 = next(g for g in params.gates if g.key == "low_factor_count")
    assert gate3.enabled is True
    assert gate3.threshold == 13

    # And it now actually fires when a real application crosses the
    # threshold -- no code change beyond the params file.
    inputs = make_valid_input()
    result = grade(inputs, params)
    below_50 = sum(1 for s in result.factor_scores.values() if s is not None and s < 50)
    fired_keys = {g.key for g in result.fired_gates}
    if below_50 >= 13:
        assert "low_factor_count" in fired_keys
    else:
        assert "low_factor_count" not in fired_keys


def test_gate_3_still_switchable_by_config_alone(params, tmp_path):
    """The switchability property T0a's predecessor test guarded --
    `evaluate_gates` reads `gate.enabled`/`gate.threshold` off the params
    file, never a hardcoded skip list -- still holds now that the gate
    ships enabled by default. Flip it back off here with no code change."""
    original_text = GRADING_PARAMS_PATH.read_text()
    switched_text = original_text.replace(
        "enabled: true, threshold: 13}",
        "enabled: false, threshold: null}",
    )
    assert switched_text != original_text  # the replace actually matched

    switched_yaml = tmp_path / "grading_params_v1.yaml"
    switched_yaml.write_text(switched_text)

    switched_params = load_params(path=switched_yaml)
    switched_gate3 = next(g for g in switched_params.gates if g.key == "low_factor_count")
    assert switched_gate3.enabled is False


def test_gate3_fire_rate_is_instrumented(params):
    """T3 acceptance criterion: gate 3 fires on 3.7-3.8% of the golden set
    at threshold 13. Runs over the full 10,000-row fixture, not the
    500-row sample -- the sample is not proportionally representative for
    this particular check (it fires at 9.6% on the sample vs 3.75% on the
    full set), so asserting this range against the sample would be
    asserting the wrong number."""
    fired = 0
    total = 0
    for row in iter_golden_set_full():
        total += 1
        inputs = row_to_grading_input(row)
        result = grade(inputs, params)
        if any(g.key == "low_factor_count" for g in result.fired_gates):
            fired += 1
    rate = fired / total
    assert 0.037 <= rate <= 0.038, f"gate 3 fire rate {rate:.4f} outside [0.037, 0.038] on the full golden set"


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
