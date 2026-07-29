"""Ingested fields -> derived raw metrics.

Spec: docs/specs/underwriting/grading-engine-core.md, R6, section 8.
"""
import statistics
from decimal import Decimal

import pytest

from app.underwriting.grading import derive

from .conftest import make_valid_input


def test_revenue_y1_is_sum_of_m13_to_m24():
    monthly = tuple(Decimal(i) for i in range(1, 25))  # m1=1 .. m24=24
    result = derive.revenue_y1_decimal(monthly)
    assert result == sum(Decimal(i) for i in range(13, 25))
    # And NOT the full 24 months, nor the prior year.
    assert result != sum(Decimal(i) for i in range(1, 25))
    assert result != sum(Decimal(i) for i in range(1, 13))


def test_total_cost_includes_cogs_as_separate_field():
    inputs = make_valid_input(
        cogs_y1=Decimal("100"),
        fixed_cost_y1=Decimal("50"),
        variable_cost_excl_cogs_y1=Decimal("30"),
    )
    # COGS is its own field, folded into total_cost directly -- not merged
    # into variable cost first, and not omitted.
    assert derive.total_cost_decimal(inputs) == Decimal("180")


def test_total_duration_revenue_is_avg_monthly_times_term():
    # A rising revenue trend, so "avg monthly x term" and "trailing N actual
    # months" give very different answers -- if the implementation used the
    # trailing-N form by mistake, this would catch it.
    values = [Decimal(str(100_000_000 + i * 20_000_000)) for i in range(24)]
    duration_months = 3
    inputs = make_valid_input(monthly_revenue=tuple(values), duration_months=duration_months)
    derived = derive.compute_derived(inputs)

    avg_monthly_revenue = derived["avg_monthly_revenue"]
    expected = float(inputs.loan_size_vnd) / (avg_monthly_revenue * duration_months)
    assert derived["loan_revenue_ratio"] == pytest.approx(expected, rel=1e-9)

    trailing_n_actual_sum = float(sum(values[-duration_months:]))
    wrong_alternative = float(inputs.loan_size_vnd) / trailing_n_actual_sum
    assert derived["loan_revenue_ratio"] != pytest.approx(wrong_alternative, rel=1e-3)


def test_volatility_uses_population_stdev_not_sample():
    trailing = [100, 110, 90, 105, 95, 100, 108, 92, 101, 99, 103, 97]
    monthly = tuple([Decimal("100")] * 12 + [Decimal(v) for v in trailing])
    # Tiny cost fields: this test's revenue figures are illustrative
    # (hundreds, not hundreds of millions) and only need profit > 0 so
    # compute_derived() doesn't raise on the unrelated SCSR guard (R8/D21).
    inputs = make_valid_input(
        monthly_revenue=monthly,
        cogs_y1=Decimal("10"),
        fixed_cost_y1=Decimal("5"),
        variable_cost_excl_cogs_y1=Decimal("5"),
    )
    derived = derive.compute_derived(inputs)

    trailing_f = [float(v) for v in trailing]
    population_stdev = statistics.pstdev(trailing_f)
    sample_stdev = statistics.stdev(trailing_f)
    assert population_stdev != sample_stdev  # sanity: the two really differ

    expected_cv = population_stdev / statistics.mean(trailing_f)
    assert derived["revenue_volatility_cv"] == pytest.approx(expected_cv, rel=1e-9)

    wrong_cv = sample_stdev / statistics.mean(trailing_f)
    assert derived["revenue_volatility_cv"] != pytest.approx(wrong_cv, rel=1e-6)


def test_revenue_trend_uses_ten_overlapping_three_month_windows():
    values = list(range(1, 25))  # m1=1 .. m24=24
    monthly = tuple(Decimal(v * 1_000_000) for v in values)
    # Tiny cost fields so profit > 0 -- see note in
    # test_volatility_uses_population_stdev_not_sample above.
    inputs = make_valid_input(
        monthly_revenue=monthly,
        cogs_y1=Decimal("1"),
        fixed_cost_y1=Decimal("1"),
        variable_cost_excl_cogs_y1=Decimal("1"),
    )
    derived = derive.compute_derived(inputs)

    floats = [v * 1_000_000.0 for v in values]
    windows = []
    for k in range(10):
        recent = sum(floats[12 + k:15 + k])  # m[13+k .. 15+k]
        prior = sum(floats[k:k + 3])  # m[1+k .. 3+k]
        windows.append((recent - prior) / prior)
    expected = statistics.mean(windows)

    assert derived["revenue_trend_decimal"] == pytest.approx(expected, rel=1e-9)
    assert len(windows) == 10

    # Not a mean of twelve monthly YoY ratios.
    wrong_alternative = statistics.mean((floats[12 + k] - floats[k]) / floats[k] for k in range(12))
    assert derived["revenue_trend_decimal"] != pytest.approx(wrong_alternative, rel=1e-6)


def test_seasonality_is_max_over_min_of_trailing_twelve():
    trailing = [100, 120, 90, 110, 105, 95, 130, 85, 115, 108, 102, 80]
    monthly = tuple([Decimal("999")] * 12 + [Decimal(v) for v in trailing])
    # Tiny cost fields so profit > 0 -- see note in
    # test_volatility_uses_population_stdev_not_sample above.
    inputs = make_valid_input(
        monthly_revenue=monthly,
        cogs_y1=Decimal("10"),
        fixed_cost_y1=Decimal("5"),
        variable_cost_excl_cogs_y1=Decimal("5"),
    )
    derived = derive.compute_derived(inputs)

    assert derived["seasonality_ratio"] == pytest.approx(max(trailing) / min(trailing), rel=1e-9)


def test_rti_composite_weights_are_50_30_20():
    inputs = make_valid_input(crr=80.0, rri=40.0, tcp=20.0)
    derived = derive.compute_derived(inputs)
    assert derived["rti"] == pytest.approx(0.5 * 80.0 + 0.3 * 40.0 + 0.2 * 20.0, rel=1e-9)

    inputs_missing = make_valid_input(crr=80.0, rri=None, tcp=20.0)
    derived_missing = derive.compute_derived(inputs_missing)
    assert derived_missing["rti"] is None
