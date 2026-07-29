"""Curve primitives.

Spec: docs/specs/underwriting/grading-engine-core.md, R2, section 8.
"""
import pytest

from app.underwriting.grading import curves


def test_sigmoid_decreasing_direction():
    low_x = curves.sigmoid(1.0, upper=100.0, steepness=1.0, intercept=5.0, decreasing=True)
    high_x = curves.sigmoid(10.0, upper=100.0, steepness=1.0, intercept=5.0, decreasing=True)
    assert high_x < low_x


def test_sigmoid_increasing_direction():
    low_x = curves.sigmoid(1.0, upper=100.0, steepness=1.0, intercept=5.0, decreasing=False)
    high_x = curves.sigmoid(10.0, upper=100.0, steepness=1.0, intercept=5.0, decreasing=False)
    assert high_x > low_x


def test_sigmoid_true_midpoint_is_intercept_over_steepness():
    # `intercept` is NOT the midpoint (R2). At x = intercept/steepness, the
    # exponent is exactly 0 for either sign, so score == upper/2 before
    # clamping. Use the real gross_margin factor constants (upper=100, so
    # upper/2 = 50 is safely inside the clamp).
    steepness, intercept, upper = 0.168, 3.024, 100.0
    true_midpoint = intercept / steepness
    score = curves.sigmoid(true_midpoint, upper=upper, steepness=steepness, intercept=intercept, decreasing=False)
    assert score == pytest.approx(upper / 2, rel=1e-9)

    # And the intercept itself is NOT the midpoint -- scoring at x=intercept
    # gives a different (in this case much higher) value.
    score_at_intercept_value = curves.sigmoid(intercept, upper=upper, steepness=steepness, intercept=intercept, decreasing=False)
    assert score_at_intercept_value != pytest.approx(upper / 2, rel=1e-6)


def test_upper_above_100_is_clamped_not_truncated_in_params(params):
    factors_with_high_upper = [f for f in params.factors if f.upper is not None and f.upper > 100.0]
    # R2/R7: several factors have `upper` above 100, up to 168.6 (seasonality).
    # The YAML is authoritative (R2) -- assert against what it actually
    # contains rather than a count transcribed from spec prose.
    assert len(factors_with_high_upper) >= 1
    assert max(f.upper for f in factors_with_high_upper) == pytest.approx(168.61289)

    for factor in factors_with_high_upper:
        # The YAML value itself is untouched -- still above 100.
        assert factor.upper > 100.0

        # Drive x toward the curve's asymptote (raw -> upper) and confirm the
        # *score* still clamps to 100, rather than the params file's `upper`
        # having been silently rounded down to 100 somewhere.
        x = -1_000_000.0 if factor.decreasing else 1_000_000.0
        score = curves.sigmoid(
            x,
            upper=factor.upper,
            steepness=factor.steepness,
            intercept=factor.intercept,
            decreasing=bool(factor.decreasing),
        )
        assert score == 100.0


def test_cubic_owner_withdrawal_matches_band_anchors(params):
    factor = next(f for f in params.factors if f.key == "owner_withdrawal")
    assert factor.kind == "cubic"

    score_at_0_2 = curves.cubic(0.2, a=factor.a, b=factor.b, c=factor.c, d=factor.d)
    score_at_1_0 = curves.cubic(1.0, a=factor.a, b=factor.b, c=factor.c, d=factor.d)

    assert score_at_0_2 == pytest.approx(99.0, abs=0.1)
    assert score_at_1_0 == pytest.approx(0.0, abs=0.1)
