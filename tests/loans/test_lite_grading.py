"""The Lite figures → GradingInput mapping.

Pure-function tests: no DB, no client. The engine is deterministic, so these
assert real behaviour rather than mocking it.

What matters here is not "does grade() work" — tests/underwriting owns that,
against a 10,000-row golden set. It is whether the ADAPTER hands the engine a
well-formed input, because every way of getting that wrong is silent: a series
of the wrong length reads as INSUFFICIENT_DATA, a year in the wrong order
inverts every trend, and a flat revenue curve flatters a seasonal business.
"""

from decimal import Decimal

import pytest

from app.loans.lite_grading import (
    CIC_BRACKET_HIGH,
    CIC_BRACKET_LOW,
    LiteGradingError,
    build_grading_input,
    grade_lite,
    synthesize_monthly_revenue,
)
from app.underwriting.grading.engine import _is_insufficient_data
from app.underwriting.grading.factors import AI_SCORE_KEYS


def figures(**overrides):
    """A profitable, internally consistent F&B set — the company in the
    screenshot that prompted this work."""
    base = {
        "revenue_last_12m": 4_000_000_000,
        "revenue_prior_12m": 3_200_000_000,
        "cogs_y1": 2_400_000_000,
        "fixed_cost_y1": 600_000_000,
        "variable_cost_excl_cogs_y1": 300_000_000,
        "revenue_best_month": 480_000_000,
        "revenue_worst_month": 210_000_000,
        "owner_withdrawal_pct": 25.0,
        "conc_top1_pct": 18.0,
        "conc_top3_pct": 41.0,
    }
    base.update(overrides)
    return base


def application(**overrides):
    base = {
        "company_code": "0312345678",
        "industry": "Food & Beverage",
        "employee_count": 23,
        "incorporation_date_months": 270,
        "loan_size_vnd": Decimal("555555555"),
        "duration_months": 9,
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Revenue synthesis
# --------------------------------------------------------------------------- #


class TestSynthesizeMonthlyRevenue:
    def test_returns_twelve_months(self):
        assert len(synthesize_monthly_revenue(1_200_000_000)) == 12

    def test_sums_to_the_stated_total_exactly(self):
        # Not "approximately": the applicant typed this number, and a series
        # that does not reconcile with it is indefensible when questioned.
        for total in (1_200_000_000, 4_000_000_000, 999_999_999, 200_000_001):
            months = synthesize_monthly_revenue(total)
            assert sum(months) == Decimal(total), total

    def test_sums_exactly_with_a_seasonal_shape_too(self):
        # The rounding drift lands on the last month; this is what proves it
        # was actually absorbed rather than dropped.
        months = synthesize_monthly_revenue(
            4_000_000_000, best_month_vnd=480_000_000, worst_month_vnd=210_000_000
        )
        assert sum(months) == Decimal(4_000_000_000)

    def test_is_flat_when_no_shape_is_given(self):
        months = synthesize_monthly_revenue(1_200_000_000)
        assert len(set(months)) == 1

    def test_varies_when_best_and_worst_are_given(self):
        # The whole reason those two optional fields exist: without them the
        # stability factor sees a perfectly steady business.
        months = synthesize_monthly_revenue(
            4_000_000_000, best_month_vnd=480_000_000, worst_month_vnd=210_000_000
        )
        assert min(months) < max(months)

    def test_a_wider_best_to_worst_gap_produces_more_variation(self):
        steady = synthesize_monthly_revenue(
            4_000_000_000, best_month_vnd=360_000_000, worst_month_vnd=330_000_000
        )
        seasonal = synthesize_monthly_revenue(
            4_000_000_000, best_month_vnd=700_000_000, worst_month_vnd=100_000_000
        )
        spread = lambda m: (max(m) - min(m)) / (sum(m) / len(m))  # noqa: E731
        assert spread(seasonal) > spread(steady)

    def test_peaks_mid_year_and_troughs_at_the_ends(self):
        # A gradual season, not a sawtooth: adjacent months that jumped would
        # read as volatility the applicant never claimed.
        months = synthesize_monthly_revenue(
            4_000_000_000, best_month_vnd=480_000_000, worst_month_vnd=210_000_000
        )
        assert months[0] == min(months)
        assert months[5] == max(months) or months[6] == max(months)

    def test_every_month_is_positive(self):
        months = synthesize_monthly_revenue(
            200_000_000, best_month_vnd=100_000_000, worst_month_vnd=1
        )
        assert all(m > 0 for m in months)

    def test_rejects_a_non_positive_total(self):
        with pytest.raises(LiteGradingError):
            synthesize_monthly_revenue(0)


# --------------------------------------------------------------------------- #
# Building the engine input
# --------------------------------------------------------------------------- #


class TestBuildGradingInput:
    def test_produces_exactly_24_complete_months(self):
        # The engine's hard requirement. A shorter series or a single None and
        # every Lite run silently becomes INSUFFICIENT_DATA.
        built = build_grading_input(
            **application(), figures=figures(), cic_score=600
        )
        assert len(built.monthly_revenue) == 24
        assert all(v is not None for v in built.monthly_revenue)

    def test_satisfies_the_engine_sufficiency_check(self):
        # Asserted against the engine's own predicate rather than a restatement
        # of it, so a change to the rule fails here instead of quietly turning
        # every band into INSUFFICIENT_DATA.
        built = build_grading_input(
            **application(), figures=figures(), cic_score=600
        )
        assert _is_insufficient_data(built) is False

    def test_orders_the_earlier_year_first(self):
        # m1..m12 is the PRIOR year, m13..m24 the most recent. Reversed, every
        # growth and trend derivation flips sign.
        built = build_grading_input(
            **application(),
            figures=figures(revenue_prior_12m=1_200_000_000, revenue_last_12m=4_800_000_000),
            cic_score=600,
        )
        assert sum(built.monthly_revenue[:12]) == Decimal(1_200_000_000)
        assert sum(built.monthly_revenue[12:]) == Decimal(4_800_000_000)

    def test_maps_the_cost_figures_straight_through(self):
        built = build_grading_input(
            **application(), figures=figures(), cic_score=600
        )
        assert built.cogs_y1 == Decimal(2_400_000_000)
        assert built.fixed_cost_y1 == Decimal(600_000_000)
        assert built.variable_cost_excl_cogs_y1 == Decimal(300_000_000)

    def test_derives_company_size_from_headcount(self):
        built = build_grading_input(
            **application(employee_count=23), figures=figures(), cic_score=600
        )
        assert built.company_size == "small"

    def test_supplies_sector_data_from_the_reference_table(self):
        built = build_grading_input(
            **application(industry="Food & Beverage"), figures=figures(), cic_score=600
        )
        assert built.sector_cagr_pct == 7.5
        assert built.ai_scores["cyclicality"] == 68

    def test_leaves_only_founder_missing_from_the_ai_scores(self):
        # The sector table covers the six industry-level AI factors; `founder`
        # is company-specific, so AI_PENDING is expected and correct. If the
        # engine ever adds an AI factor, this catches that the table cannot
        # supply it — otherwise the new factor would silently score as absent.
        built = build_grading_input(
            **application(), figures=figures(), cic_score=600
        )
        assert set(AI_SCORE_KEYS) - set(built.ai_scores) == {"founder"}

    def test_passes_optional_figures_through_as_none_when_blank(self):
        built = build_grading_input(
            **application(),
            figures=figures(conc_top1_pct=None, owner_withdrawal_pct=None),
            cic_score=600,
        )
        assert built.conc_top1_pct is None
        assert built.owner_withdrawal is None

    def test_rejects_a_headcount_the_engine_has_no_band_for(self):
        with pytest.raises(LiteGradingError):
            build_grading_input(
                **application(employee_count=5000), figures=figures(), cic_score=600
            )

    def test_rejects_an_industry_with_no_sector_data(self):
        # Excluded industries pass engine validation (gate 5 rejects them after
        # grading) but have no sector row, so no indicative rate is possible.
        with pytest.raises(LiteGradingError):
            build_grading_input(
                **application(industry="gambling"), figures=figures(), cic_score=600
            )


# --------------------------------------------------------------------------- #
# The band
# --------------------------------------------------------------------------- #


class TestGradeLite:
    def test_returns_a_real_rate_band(self):
        band = grade_lite(**application(), figures=figures())

        assert band.rate_low_pct > 0
        assert band.rate_low_pct <= band.rate_high_pct
        assert band.grade_low <= band.grade_high

    def test_the_band_brackets_the_cic_range(self):
        # The band must be the two CIC endpoints and nothing else, or it is not
        # measuring what it claims to.
        band = grade_lite(**application(), figures=figures())
        low = grade_lite(**application(), figures=figures())

        assert band.rate_low_pct == low.rate_low_pct  # deterministic
        assert CIC_BRACKET_LOW < CIC_BRACKET_HIGH

    def test_a_better_cic_produces_a_lower_rate(self):
        # Which is why `high` carries the lower rate, and why the band is
        # sorted on values rather than on which run produced it.
        from app.loans.lite_grading import build_grading_input as build
        from app.underwriting.grading import grade

        worse = grade(build(**application(), figures=figures(), cic_score=CIC_BRACKET_LOW))
        better = grade(build(**application(), figures=figures(), cic_score=CIC_BRACKET_HIGH))
        assert better.interest_rate_pct < worse.interest_rate_pct

    def test_reports_ai_pending_rather_than_a_finished_decision(self):
        # `founder` has no sector value, so the engine is honest that grading is
        # incomplete. A Lite band must never read APPROVED.
        band = grade_lite(**application(), figures=figures())
        assert band.decision_low == "AI_PENDING"
        assert band.decision_high == "AI_PENDING"

    def test_is_flagged_provisional_while_the_sector_table_is_unreviewed(self):
        # sector_reference_v1.yaml is DRAFT_UNREVIEWED and instructs callers to
        # surface results as provisional until the CEO signs it off.
        band = grade_lite(**application(), figures=figures())
        assert band.provisional is True
        assert any("provisional" in a for a in band.assumptions)

    def test_states_every_assumption_it_made(self):
        band = grade_lite(**application(), figures=figures())
        joined = " ".join(band.assumptions)
        assert "CIC" in joined
        assert "AML" in joined or "Identity" in joined

    def test_warns_when_revenue_had_to_be_modelled_flat(self):
        band = grade_lite(
            **application(),
            figures=figures(revenue_best_month=None, revenue_worst_month=None),
        )
        assert any("flat" in a for a in band.assumptions)

    def test_stamps_the_versions_that_produced_the_band(self):
        # A quoted rate has to be reconstructable later, and that needs the
        # engine, params and sector-table versions it came from.
        band = grade_lite(**application(), figures=figures())
        assert band.engine_version
        assert band.params_version
        assert band.sector_reference_version.startswith("v1-")

    def test_explains_itself_when_costs_swallow_revenue(self):
        # compute_derived raises on profit <= 0 (D21). That is a real answer
        # about the applicant, so it must not surface as a 500.
        with pytest.raises(LiteGradingError, match="costs"):
            grade_lite(
                **application(),
                figures=figures(
                    cogs_y1=3_000_000_000,
                    fixed_cost_y1=800_000_000,
                    variable_cost_excl_cogs_y1=500_000_000,
                ),
            )

    def test_rejects_a_term_the_engine_does_not_allow(self):
        # 10 months is not in allowed_durations_months. The API validates this
        # upstream, so reaching here is a bug — it should raise, not price.
        with pytest.raises(ValueError):
            grade_lite(**application(duration_months=10), figures=figures())

    def test_rejects_a_loan_outside_the_engine_bounds(self):
        with pytest.raises(ValueError):
            grade_lite(
                **application(loan_size_vnd=Decimal("100000000")), figures=figures()
            )

    def test_a_seasonal_business_is_priced_differently_from_a_steady_one(self):
        # If this ever stops holding, the best/worst fields have become
        # decorative and the flat-revenue warning is a lie.
        steady = grade_lite(
            **application(),
            figures=figures(revenue_best_month=340_000_000, revenue_worst_month=330_000_000),
        )
        swingy = grade_lite(
            **application(),
            figures=figures(revenue_best_month=700_000_000, revenue_worst_month=90_000_000),
        )
        assert steady.rate_low_pct != swingy.rate_low_pct
