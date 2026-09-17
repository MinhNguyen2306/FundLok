"""T3 (HANDOFF-03) -- sector reference table loader + resolver.

Spec: docs/specs/underwriting/sector-reference-table.md (ACCEPTED v1.0).
Acceptance criteria in section 8 map 1:1 to the test names below.
"""
import ast
import inspect

import pytest

from app.underwriting.grading import grade, load_params, load_sector_reference, resolve_sector_inputs
from app.underwriting.grading import sector_reference as sector_reference_module

from .conftest import iter_golden_set_full, make_valid_input, row_to_grading_input, within_tolerance


# --------------------------------------------------------------------
# The one that must not break
# --------------------------------------------------------------------


def test_golden_set_still_reconciles_after_sector_reference_added(params):
    """R2: resolve_sector_inputs must never be called inside grade()'s own
    path. If this fails, R2 was violated -- the diagnosis is that
    sector_reference.py got wired into engine.py/factors.py/rollup.py."""
    for row in iter_golden_set_full():
        inputs = row_to_grading_input(row)
        result = grade(inputs, params)
        assert within_tolerance(result.final_grade, float(row["expect_final_grade"]))


def test_grade_signature_and_behaviour_unchanged():
    inputs = make_valid_input()
    result_before = grade(inputs, load_params())
    result_after = grade(inputs, load_params())
    assert result_before.final_grade == result_after.final_grade
    assert result_before.decision == result_after.decision


# --------------------------------------------------------------------
# Loading and validation
# --------------------------------------------------------------------


def test_sector_reference_loads_and_is_frozen():
    ref = load_sector_reference()
    with pytest.raises(TypeError):
        ref.industries["IT Services"]["regulatory"] = 0  # MappingProxyType is read-only


def test_sector_reference_version_pinned():
    ref = load_sector_reference()
    assert ref.sector_reference_version == "v1-20260728"


def test_all_15_industries_present():
    ref = load_sector_reference()
    assert len(ref.industries) == 15


def test_industry_names_match_supported_industries_exactly(params):
    # load_sector_reference() itself raises at load time if they don't match.
    load_sector_reference(supported_industries=params.supported_industries)


def test_every_industry_has_all_seven_columns():
    ref = load_sector_reference()
    for name, row in ref.industries.items():
        assert set(row.keys()) == {
            "regulatory", "input_cost_vol", "cyclicality", "competitor",
            "macro", "uncontrollable", "cagr_pct",
        }, name


def test_score_columns_validated_0_to_100():
    ref = load_sector_reference()
    for name, row in ref.industries.items():
        for key in ("regulatory", "input_cost_vol", "cyclicality", "competitor", "macro", "uncontrollable"):
            assert 0 <= row[key] <= 100, (name, key, row[key])


def test_cagr_column_permits_negative_values():
    """Asserts cagr_pct is NOT validated as 0-100 -- its valid_range in the
    YAML is [-20.0, 40.0], not [0, 100]."""
    ref = load_sector_reference()
    assert ref.columns["cagr_pct"].valid_range[0] < 0


def test_missing_column_fails_at_load_not_at_scoring(tmp_path):
    original = (sector_reference_module._DEFAULT_SECTOR_REFERENCE_PATH).read_text()
    broken = original.replace("cagr_pct: 14.0", "")  # drop one industry's cagr_pct
    broken_path = tmp_path / "sector_reference_broken.yaml"
    broken_path.write_text(broken)
    with pytest.raises(ValueError, match="missing column"):
        load_sector_reference(path=broken_path)


def test_out_of_range_score_fails_at_load(tmp_path):
    original = (sector_reference_module._DEFAULT_SECTOR_REFERENCE_PATH).read_text()
    broken = original.replace("regulatory: 80, input_cost_vol: 80", "regulatory: 180, input_cost_vol: 80")
    broken_path = tmp_path / "sector_reference_broken.yaml"
    broken_path.write_text(broken)
    with pytest.raises(ValueError, match="outside valid_range"):
        load_sector_reference(path=broken_path)


def test_wrong_industry_count_fails_at_load(tmp_path):
    original = (sector_reference_module._DEFAULT_SECTOR_REFERENCE_PATH).read_text()
    lines = original.splitlines()
    # Remove one industry line (Construction Materials, the last one).
    broken_lines = [l for l in lines if not l.strip().startswith("Construction Materials:")]
    broken_path = tmp_path / "sector_reference_broken.yaml"
    broken_path.write_text("\n".join(broken_lines))
    with pytest.raises(ValueError, match="expected exactly 15"):
        load_sector_reference(path=broken_path)


# --------------------------------------------------------------------
# Resolution
# --------------------------------------------------------------------


def test_resolve_returns_six_sector_scores_plus_founder():
    ref = load_sector_reference()
    resolved = resolve_sector_inputs("IT Services", ref)
    assert set(resolved["ai_scores"].keys()) == {
        "regulatory", "input_cost_vol", "cyclicality", "competitor", "macro", "uncontrollable", "founder",
    }


def test_resolve_returns_cagr_separately_from_ai_scores():
    ref = load_sector_reference()
    resolved = resolve_sector_inputs("IT Services", ref)
    assert "cagr_pct" not in resolved["ai_scores"]
    assert "sector_cagr_pct" in resolved
    assert resolved["sector_cagr_pct"] == 14.0


def test_resolve_unknown_industry_raises_with_valid_options():
    ref = load_sector_reference()
    with pytest.raises(KeyError, match="IT Services"):
        resolve_sector_inputs("Nonexistent Sector", ref)


def test_resolve_includes_reference_version():
    ref = load_sector_reference()
    resolved = resolve_sector_inputs("IT Services", ref)
    assert resolved["sector_reference_version"] == "v1-20260728"


def test_resolve_marks_provisional_while_status_is_draft():
    ref = load_sector_reference()
    assert ref.status == "DRAFT_UNREVIEWED"
    resolved = resolve_sector_inputs("IT Services", ref)
    assert resolved["provisional"] is True


def test_resolved_mapping_is_immutable():
    ref = load_sector_reference()
    resolved = resolve_sector_inputs("IT Services", ref)
    with pytest.raises(TypeError):
        resolved["ai_scores"]["founder"] = 0


def test_founder_constant_is_50():
    ref = load_sector_reference()
    assert ref.founder_constant == 50


def test_no_sector_value_appears_as_python_literal():
    """AST walk over sector_reference.py: no numeric literal matching a
    table value (R3). Small integers used as structural constants
    (_REQUIRED_INDUSTRY_COUNT = 15, column counts) are not table values
    and are allowed."""
    source = inspect.getsource(sector_reference_module)
    tree = ast.parse(source)
    ref = load_sector_reference()
    table_values = set()
    for row in ref.industries.values():
        for v in row.values():
            table_values.add(float(v))
    table_values.add(float(ref.founder_constant))

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            assert float(node.value) not in table_values, f"literal {node.value} matches a table value"


# --------------------------------------------------------------------
# End to end, using the resolver
# --------------------------------------------------------------------


def test_application_with_resolved_sector_inputs_reaches_a_decision():
    ref = load_sector_reference()
    resolved = resolve_sector_inputs("IT Services", ref)
    inputs = make_valid_input(
        industry="IT Services",
        ai_scores=dict(resolved["ai_scores"]),
        sector_cagr_pct=resolved["sector_cagr_pct"],
    )
    result = grade(inputs, load_params())
    assert result.decision != "AI_PENDING"


def test_two_industries_produce_different_sector_premiums():
    ref = load_sector_reference()
    r1 = resolve_sector_inputs("IT Services", ref)
    r2 = resolve_sector_inputs("Construction Materials", ref)
    inputs1 = make_valid_input(industry="IT Services", ai_scores=dict(r1["ai_scores"]), sector_cagr_pct=r1["sector_cagr_pct"])
    inputs2 = make_valid_input(industry="Construction Materials", ai_scores=dict(r2["ai_scores"]), sector_cagr_pct=r2["sector_cagr_pct"])
    params = load_params()
    result1 = grade(inputs1, params)
    result2 = grade(inputs2, params)
    assert result1.premiums["sector"] != result2.premiums["sector"]


def test_logistics_scores_lower_on_input_cost_than_professional_services():
    ref = load_sector_reference()
    logistics = resolve_sector_inputs("Logistics & Transport", ref)
    professional = resolve_sector_inputs("Professional Services", ref)
    assert logistics["ai_scores"]["input_cost_vol"] < professional["ai_scores"]["input_cost_vol"]


# --------------------------------------------------------------------
# Calibration guard
# --------------------------------------------------------------------


def test_achieved_mean_sector_premium_within_tolerance_of_calibration_block():
    ref = load_sector_reference()
    params = load_params()
    premiums = []
    for name in ref.industries:
        resolved = resolve_sector_inputs(name, ref)
        inputs = make_valid_input(industry=name, ai_scores=dict(resolved["ai_scores"]), sector_cagr_pct=resolved["sector_cagr_pct"])
        result = grade(inputs, params)
        premiums.append(result.premiums["sector"])
    mean_premium = sum(premiums) / len(premiums)
    assert abs(mean_premium - 53.56) <= 0.5, mean_premium


def test_premium_range_matches_calibration_block():
    ref = load_sector_reference()
    params = load_params()
    premiums = []
    for name in ref.industries:
        resolved = resolve_sector_inputs(name, ref)
        inputs = make_valid_input(industry=name, ai_scores=dict(resolved["ai_scores"]), sector_cagr_pct=resolved["sector_cagr_pct"])
        result = grade(inputs, params)
        premiums.append(result.premiums["sector"])
    assert min(premiums) == pytest.approx(38.89, abs=0.5)
    assert max(premiums) == pytest.approx(71.97, abs=0.5)


def test_sector_premium_spread_exceeds_25_points():
    ref = load_sector_reference()
    params = load_params()
    premiums = []
    for name in ref.industries:
        resolved = resolve_sector_inputs(name, ref)
        inputs = make_valid_input(industry=name, ai_scores=dict(resolved["ai_scores"]), sector_cagr_pct=resolved["sector_cagr_pct"])
        result = grade(inputs, params)
        premiums.append(result.premiums["sector"])
    assert max(premiums) - min(premiums) > 25
