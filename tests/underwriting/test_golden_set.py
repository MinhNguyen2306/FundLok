"""Golden-set reconciliation.

Spec: docs/specs/underwriting/grading-engine-core.md, section 8.
Tolerance: abs(actual - expected) <= max(1e-6, abs(expected) * 1e-7).
"""
from app.underwriting.grading import grade

from .conftest import (
    FACTOR_EXPECT_COLUMNS,
    PREMIUM_EXPECT_COLUMNS,
    iter_golden_set_full,
    iter_golden_set_sample,
    row_to_grading_input,
    within_tolerance,
)


def test_golden_set_full_reconciles_all_10000_rows(params):
    """THE ONE THAT MATTERS MOST. For every row in golden_set.csv.gz, all 22
    factor scores, all 4 premiums and the final grade match within tolerance.

    This test passing is the definition of done. It is known-passable: the
    same YAML and fixture have been reconciled independently, 270,000
    assertions, zero failures. If it fails, the implementation is wrong, not
    the fixture -- do not reduce the row count, loosen the tolerance, mark it
    xfail, or skip it.
    """
    rows_checked = 0

    for row in iter_golden_set_full():
        rows_checked += 1
        inputs = row_to_grading_input(row)
        result = grade(inputs, params)

        for factor_key, expect_col in FACTOR_EXPECT_COLUMNS.items():
            expected = float(row[expect_col])
            actual = result.factor_scores[factor_key]
            assert actual is not None, (
                f"row {rows_checked} ({row['company_code']}): {factor_key} scored None, "
                f"expected {expected}"
            )
            assert within_tolerance(actual, expected), (
                f"row {rows_checked} ({row['company_code']}): {factor_key} = {actual}, "
                f"expected {expected}"
            )

        for premium_key, expect_col in PREMIUM_EXPECT_COLUMNS.items():
            expected = float(row[expect_col])
            actual = result.premiums[premium_key]
            assert within_tolerance(actual, expected), (
                f"row {rows_checked} ({row['company_code']}): {premium_key} premium = {actual}, "
                f"expected {expected}"
            )

        expected_final_grade = float(row["expect_final_grade"])
        assert within_tolerance(result.final_grade, expected_final_grade), (
            f"row {rows_checked} ({row['company_code']}): final_grade = {result.final_grade}, "
            f"expected {expected_final_grade}"
        )

    assert rows_checked == 10000


def test_all_factor_scores_within_0_100(params):
    checked_any = False
    for row in iter_golden_set_sample():
        checked_any = True
        inputs = row_to_grading_input(row)
        result = grade(inputs, params)
        for factor_key, score in result.factor_scores.items():
            if score is not None:
                assert 0.0 <= score <= 100.0, f"{row['company_code']}: {factor_key} = {score}"
    assert checked_any
