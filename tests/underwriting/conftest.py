"""Shared fixtures/helpers for the grading engine test suite.

Spec: docs/specs/underwriting/grading-engine-core.md (ACCEPTED v1.0).
Fixtures: tests/underwriting/fixtures/golden_set.csv.gz (10,000 rows),
golden_set_sample.csv (500 rows). Both are DO NOT TOUCH -- verified,
authoritative, and read-only from here.
"""
from __future__ import annotations

import csv
import gzip
from decimal import Decimal
from pathlib import Path
from typing import Dict, Iterator

import pytest

from app.underwriting import grading
from app.underwriting.grading import GradingInput, load_params

FIXTURES_DIR = Path(__file__).parent / "fixtures"
GOLDEN_SET_GZ = FIXTURES_DIR / "golden_set.csv.gz"
GOLDEN_SET_SAMPLE = FIXTURES_DIR / "golden_set_sample.csv"

# Path to the real params YAML on disk -- used only by the two gate-switch
# tests, to prove gates 3/7 are switchable by config (a modified copy of this
# file) with zero code changes.
GRADING_PARAMS_PATH = Path(grading.__file__).parent / "params" / "grading_params_v1.yaml"

COMPANY_SIZE_MAP = {
    "Micro (1-10)": "micro",
    "Small (11-50)": "small",
    "Medium (51-200)": "medium",
}

AI_SCORE_CSV_COLUMNS = {
    "regulatory": "regulatory_raw",
    "input_cost_vol": "input_cost_vol_raw",
    "cyclicality": "cyclicality_raw",
    "competitor": "competitor_raw",
    "macro": "macro_raw",
    "uncontrollable": "uncontrollable_raw",
    "founder": "founder_raw",
}

# factor key -> golden set `expect_*` column
FACTOR_EXPECT_COLUMNS = {
    "gross_margin": "expect_gross_margin",
    "contribution_margin": "expect_contribution_margin",
    "operating_margin": "expect_operating_margin",
    "cost_flexibility": "expect_cost_flexibility",
    "loan_revenue": "expect_loan_revenue",
    "scsr": "expect_scsr",
    "revenue_volatility": "expect_revenue_volatility",
    "revenue_trend": "expect_revenue_trend",
    "conc_top1": "expect_conc_top1",
    "conc_top3": "expect_conc_top3",
    "seasonality": "expect_seasonality",
    "revenue_type": "expect_revenue_type",
    "sector_growth": "expect_sector_growth",
    "regulatory": "expect_regulatory",
    "input_cost_vol": "expect_input_cost_vol",
    "cyclicality": "expect_cyclicality",
    "competitor": "expect_competitor",
    "macro": "expect_macro",
    "uncontrollable": "expect_uncontrollable",
    "owner_withdrawal": "expect_owner_withdrawal",
    "founder": "expect_founder",
    "cic": "expect_cic",
}

PREMIUM_EXPECT_COLUMNS = {
    "bcq": "expect_bcq",
    "rsg": "expect_rsg",
    "sector": "expect_sector",
    "behavioral": "expect_behavioral",
}

# Spec section 8: abs(actual - expected) <= max(1e-6, abs(expected) * 1e-7)
TOLERANCE_ABS = 1e-6
TOLERANCE_REL = 1e-7


def within_tolerance(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= max(TOLERANCE_ABS, abs(expected) * TOLERANCE_REL)


def row_to_grading_input(row: Dict[str, str]) -> GradingInput:
    """Map one golden-set CSV row onto a `GradingInput`. `operating_months`
    and `kyc_aml_passed`/`fraud_flags` have no column in the fixture (the
    golden set only reconciles factor scores/premiums/final grade, not gates
    or pricing -- see R10 and deviations register D13) so they're filled
    with values that keep gates out of the way rather than invented data."""
    monthly_revenue = tuple(Decimal(row[f"m{i}"]) for i in range(1, 25))
    ai_scores = {key: float(row[col]) for key, col in AI_SCORE_CSV_COLUMNS.items()}
    return GradingInput(
        company_code=row["company_code"],
        industry=row["industry"],
        company_size=COMPANY_SIZE_MAP[row["company_size"]],
        loan_size_vnd=Decimal(row["loan_size"]),
        duration_months=int(float(row["duration_months"])),
        operating_months=999,
        monthly_revenue=monthly_revenue,
        cogs_y1=Decimal(row["cogs_y1"]),
        fixed_cost_y1=Decimal(row["fixed_cost_y1"]),
        variable_cost_excl_cogs_y1=Decimal(row["variable_cost_excl_cogs_y1"]),
        conc_top1_pct=float(row["conc_top1_pct"]),
        conc_top3_pct=float(row["conc_top3_pct"]),
        crr=float(row["crr"]),
        rri=float(row["rri"]),
        tcp=float(row["tcp"]),
        sector_cagr_pct=float(row["sector_cagr_pct"]),
        ai_scores=ai_scores,
        owner_withdrawal=float(row["owner_withdrawal_raw"]),
        cic_score=int(float(row["cic_score"])),
        kyc_aml_passed=True,
        fraud_flags=(),
        bank_rate_pct=float(row["bank_rate_pct"]),
    )


def iter_golden_set_full() -> Iterator[Dict[str, str]]:
    with gzip.open(GOLDEN_SET_GZ, "rt", newline="") as fh:
        yield from csv.DictReader(fh)


def iter_golden_set_sample() -> Iterator[Dict[str, str]]:
    with open(GOLDEN_SET_SAMPLE, "r", newline="") as fh:
        yield from csv.DictReader(fh)


def first_golden_row() -> Dict[str, str]:
    """SME-0001 -- the spec's worked example (final_grade 70.98376463)."""
    with gzip.open(GOLDEN_SET_GZ, "rt", newline="") as fh:
        return next(csv.DictReader(fh))


def make_valid_input(**overrides) -> GradingInput:
    """A hand-built, fully-scorable `GradingInput` with sane defaults. Tests
    that need "some valid application" start here and override only the
    field(s) they care about."""
    defaults = dict(
        company_code="SME-TEST-0001",
        industry="IT Services",
        company_size="micro",
        loan_size_vnd=Decimal("3000000000"),
        duration_months=3,
        operating_months=36,
        monthly_revenue=tuple(Decimal("100000000") for _ in range(24)),
        cogs_y1=Decimal("500000000"),
        fixed_cost_y1=Decimal("200000000"),
        variable_cost_excl_cogs_y1=Decimal("100000000"),
        conc_top1_pct=30.0,
        conc_top3_pct=50.0,
        crr=60.0,
        rri=60.0,
        tcp=60.0,
        sector_cagr_pct=10.0,
        ai_scores={
            "regulatory": 60.0,
            "input_cost_vol": 60.0,
            "cyclicality": 60.0,
            "competitor": 60.0,
            "macro": 60.0,
            "uncontrollable": 60.0,
            "founder": 60.0,
        },
        owner_withdrawal=50.0,
        cic_score=650,
        kyc_aml_passed=True,
        fraud_flags=(),
        bank_rate_pct=12.0,
    )
    defaults.update(overrides)
    return GradingInput(**defaults)


@pytest.fixture(scope="session")
def params():
    return load_params()


@pytest.fixture(scope="session")
def golden_row():
    return first_golden_row()
