"""Map the Lite figures an SME types onto the grading engine's `GradingInput`.

WHY THIS EXISTS
`grade(inputs, params)` is a pure function that takes 21 already-normalised
fields. The Lite flow collects 10 numbers. This module is the adapter between
them, and it is the whole reason a typed-figures flow can return an interest
band at all.

WHERE IT LIVES
`app/loans/`, not `app/underwriting/`. The engine is imported read-only, the
same way `app/projects/engine_constraints.py` already does it — nothing here
touches Edward's module, and `start_score_run`'s real integration
(docs/specs/underwriting/grading-engine-integration.md, still DRAFT) lands
independently of this.

The sector table's own header sanctions exactly this: "DO NOT WIRE THIS INTO
grade() … It is an ALTERNATIVE input source for production callers assembling a
GradingInput." That caller is this module.

WHAT IT PRODUCES
A *band*, not a number. `_is_insufficient_data` refuses to score without a
`cic_score`, and the Lite flow deliberately does not ask for one — CIC is the
sensitive document SMEs will not hand over before signing up. So the engine is
run twice, at the bottom and top of the CIC range it was calibrated against,
and the two rates bracket the answer. That is what "predictive interest band"
means, and it invents no single figure.

THIS IS INDICATIVE, NEVER AN OFFER
Three separate reasons, all recorded on the result as `assumptions` so a caller
cannot forget them:
  * `cic_score` is bracketed, not known.
  * `kyc_aml_passed` is assumed True — gate 6 is a hard REJECT on False, so a
    pre-KYC estimate has to assume the applicant would pass. The real run
    re-evaluates it.
  * The sector table is `status: DRAFT_UNREVIEWED` with `review.reviewed_by:
    null`, and its own instruction is that "callers should surface results as
    provisional" until the CEO signs it off. Sector drives 36% of the spread.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Mapping, Optional, Tuple

import yaml

from app.projects.engine_constraints import company_size_for_headcount, params
from app.underwriting.grading import GradingInput, grade

__all__ = [
    "LiteBand",
    "LiteGradingError",
    "build_grading_input",
    "grade_lite",
    "synthesize_monthly_revenue",
]

# The CIC range the engine was actually validated against: the golden set spans
# 442-750 (see factor 20 in grading_params_v1.yaml). The generator spec allows
# 150-750, but bracketing down to 150 would extrapolate the sigmoid far below
# anything the regression suite covers and would widen the band into
# uselessness. Gate 7 (`cic_floor`, cic_score <= 500) ships DISABLED pending
# confirmation of the CIC scale, so the low end cannot spuriously hard-reject.
CIC_BRACKET_LOW = 442
CIC_BRACKET_HIGH = 750

# Assumed for the indicative run only. Gate 6 (`kyc_aml`) is a hard REJECT when
# this is False, so passing False would make every Lite band read REJECT and
# tell the applicant nothing.
ASSUMED_KYC_AML_PASSED = True

# Floor on the modelled worst-to-best month ratio. See synthesize_monthly_revenue.
MIN_SHAPE_RATIO = 0.02

_SECTOR_TABLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "underwriting"
    / "grading"
    / "params"
    / "sector_reference_v1.yaml"
)

# The six of the seven AI-graded factors that are properties of an INDUSTRY
# rather than of a company, so the sector table can supply them. `founder` is
# the seventh and is company-specific, so it stays missing and the engine
# reports AI_PENDING — by design (R3/R8), and the rate is still computed.
_SECTOR_AI_KEYS = (
    "regulatory",
    "input_cost_vol",
    "cyclicality",
    "competitor",
    "macro",
    "uncontrollable",
)


class LiteGradingError(ValueError):
    """A figure set the engine cannot score, with a reason fit to show a user.

    Distinct from the engine's own `ValueError`s: those mean the caller built a
    malformed input, which is a bug. This means the applicant's own numbers
    describe a company the engine has no rule for — most often costs at or above
    revenue, where `derive.compute_derived` raises (D21).

    Carries a `code` as well as a message because the message reaches a
    bilingual UI. The English text is the fallback and the log line; the code is
    what the frontend translates. Adding a raise site without a code means a
    Vietnamese applicant reads English, so `code` has no default.
    """

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LiteBand:
    """An indicative rate range. Never an offer — see the module docstring."""

    rate_low_pct: float
    rate_high_pct: float
    grade_low: float
    grade_high: float
    # The engine's own decision at each end. Expected to be AI_PENDING, because
    # `founder` has no sector-level value; a REJECT here is a fired hard gate
    # and is meaningful.
    decision_low: str
    decision_high: str
    engine_version: str
    params_version: str
    sector_reference_version: str
    provisional: bool
    assumptions: Tuple[str, ...]


@lru_cache(maxsize=1)
def _sector_table() -> Mapping[str, object]:
    """The sector reference table. Cached: read-only at runtime, like params()."""
    with _SECTOR_TABLE_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _sector_row(industry: str) -> Mapping[str, float]:
    table = _sector_table()
    rows = table.get("industries") or {}
    row = rows.get(industry)
    if row is None:
        # Every supported industry has a row, so this means the industry passed
        # validation as *excluded* (gambling, alcohol, …). Those are recognised
        # but unscoreable — there is deliberately no sector data for them.
        raise LiteGradingError(
            f"No sector reference data for industry {industry!r}; it cannot be "
            "given an indicative rate.",
            code="INDUSTRY_NOT_SCOREABLE",
        )
    return row


def _sector_is_reviewed() -> bool:
    review = _sector_table().get("review") or {}
    return review.get("reviewed_by") is not None


def synthesize_monthly_revenue(
    total_vnd: int,
    best_month_vnd: Optional[int] = None,
    worst_month_vnd: Optional[int] = None,
) -> Tuple[Decimal, ...]:
    """Twelve monthly figures that sum to `total_vnd`.

    The engine needs 24 months and refuses to score on a short series or any
    `None`, but no SME is going to type 24 numbers — that friction is the entire
    thing the Lite flow removes. So the annual total sets the MAGNITUDE and the
    optional best/worst months set the SHAPE.

    Shape matters because the engine scores revenue *stability*: a flat twelve
    months reads as a perfectly steady business, which flatters every applicant
    who leaves the optional fields blank. With best/worst given, this builds a
    single-peak season whose spread matches the ratio between them.

    The series is rescaled to hit the total exactly, so the literal min and max
    are not preserved — the coefficient of variation is, and that is what the
    stability factor actually reads.
    """
    if total_vnd <= 0:
        raise LiteGradingError(
            "Annual revenue must be greater than zero.",
            code="REVENUE_MUST_BE_POSITIVE",
        )

    months = 12
    have_shape = (
        best_month_vnd is not None
        and worst_month_vnd is not None
        and best_month_vnd > 0
        and worst_month_vnd <= best_month_vnd
    )

    if have_shape:
        # Floored, because the ratio is otherwise unbounded below: validation
        # only requires worst > 0 and worst <= best, so a worst month of 1 đồng
        # against a best of 100m gives a ratio near zero, the trough months
        # round to 0 đồng, and a single zero month makes
        # `min_trailing_twelve_decimal` zero — which flips the engine to
        # INSUFFICIENT_DATA and silently produces no band at all. A month at 2%
        # of the peak is already extreme seasonality, so nothing real is lost.
        ratio = max(
            worst_month_vnd / best_month_vnd,  # type: ignore[operator]
            MIN_SHAPE_RATIO,
        )
        # Triangular wave: troughs at the ends, peak mid-year. A real seasonal
        # curve rather than a sawtooth, so consecutive months move gradually —
        # month-on-month jumps would be read as volatility that the applicant
        # never claimed.
        peak = (months - 1) / 2
        weights = [1.0 - (1.0 - ratio) * (abs(i - peak) / peak) for i in range(months)]
    else:
        weights = [1.0] * months

    weight_total = sum(weights)
    raw = [Decimal(total_vnd) * Decimal(str(w / weight_total)) for w in weights]

    # Whole đồng: VND has no sub-unit, so a fractional month is meaningless.
    rounded = [max(value.quantize(Decimal("1")), Decimal(1)) for value in raw]

    # The series must sum to the stated total exactly. An off-by-a-few-đồng
    # total is harmless arithmetically but leaves the figures irreconcilable
    # with what the applicant typed, and they are being asked to act on it.
    #
    # The drift lands on the PEAK month, not the last one: the last month is a
    # trough and can be small enough that subtracting the drift would push it to
    # zero or negative, reintroducing the very problem the floor above prevents.
    peak_index = max(range(months), key=lambda i: rounded[i])
    rounded[peak_index] += Decimal(total_vnd) - sum(rounded)

    if any(value <= 0 for value in rounded):
        # Only reachable if the total is too small to spread across 12 positive
        # months at all. Raising beats returning a series the engine will refuse
        # to score for reasons the applicant could never guess.
        raise LiteGradingError(
            "Annual revenue is too small to model as twelve monthly figures.",
            code="REVENUE_TOO_SMALL",
        )

    return tuple(rounded)


def build_grading_input(
    *,
    company_code: str,
    industry: str,
    employee_count: int,
    incorporation_date_months: int,
    loan_size_vnd: Decimal,
    duration_months: int,
    figures: Mapping[str, Optional[float]],
    cic_score: int,
) -> GradingInput:
    """Assemble a `GradingInput` from the Lite figures plus the application form.

    `figures` is the stored `self_reported_figures` payload — the same keys
    `LoanApplicationFiguresIn` validates, so the contract is enforced before
    anything reaches here.
    """
    company_size = company_size_for_headcount(employee_count)
    if company_size is None:
        bands = params().company_sizes
        raise LiteGradingError(
            f"An employee count of {employee_count} is outside the sizes the "
            f"engine grades ({bands['micro']['min']}-{bands['medium']['max']}).",
            code="HEADCOUNT_OUT_OF_RANGE",
        )

    revenue_last = figures.get("revenue_last_12m")
    revenue_prior = figures.get("revenue_prior_12m")
    if not revenue_last or not revenue_prior:
        raise LiteGradingError(
            "Both years of revenue are required.",
            code="REVENUE_REQUIRED",
        )

    # m1..m12 is the EARLIER year and m13..m24 the most recent, matching the
    # ordering grading-input-sources.md ยง3.1 assigns to `monthly_revenue`.
    # Getting this backwards would invert every growth and trend derivation.
    monthly = synthesize_monthly_revenue(
        int(revenue_prior)
    ) + synthesize_monthly_revenue(
        int(revenue_last),
        best_month_vnd=_as_int(figures.get("revenue_best_month")),
        worst_month_vnd=_as_int(figures.get("revenue_worst_month")),
    )

    sector = _sector_row(industry)
    ai_scores = {key: float(sector[key]) for key in _SECTOR_AI_KEYS}

    return GradingInput(
        company_code=company_code,
        industry=industry,
        company_size=company_size,  # type: ignore[arg-type]
        loan_size_vnd=loan_size_vnd,
        duration_months=duration_months,
        operating_months=incorporation_date_months,
        monthly_revenue=monthly,
        cogs_y1=Decimal(str(figures["cogs_y1"])),
        fixed_cost_y1=Decimal(str(figures["fixed_cost_y1"])),
        variable_cost_excl_cogs_y1=Decimal(str(figures["variable_cost_excl_cogs_y1"])),
        conc_top1_pct=_as_float(figures.get("conc_top1_pct")),
        conc_top3_pct=_as_float(figures.get("conc_top3_pct")),
        # Not collected by the Lite flow and genuinely Optional in the engine:
        # they refine the score, they do not gate it.
        crr=None,
        rri=None,
        tcp=None,
        sector_cagr_pct=float(sector["cagr_pct"]),
        ai_scores=ai_scores,
        owner_withdrawal=_as_float(figures.get("owner_withdrawal_pct")),
        cic_score=cic_score,
        kyc_aml_passed=ASSUMED_KYC_AML_PASSED,
        fraud_flags=(),
    )


def _as_int(value: object) -> Optional[int]:
    return None if value is None else int(value)  # type: ignore[arg-type]


def _as_float(value: object) -> Optional[float]:
    return None if value is None else float(value)  # type: ignore[arg-type]


def grade_lite(
    *,
    company_code: str,
    industry: str,
    employee_count: int,
    incorporation_date_months: int,
    loan_size_vnd: Decimal,
    duration_months: int,
    figures: Mapping[str, Optional[float]],
) -> LiteBand:
    """Run the engine twice across the CIC range and return the resulting band."""
    p = params()

    def run(cic: int):
        inputs = build_grading_input(
            company_code=company_code,
            industry=industry,
            employee_count=employee_count,
            incorporation_date_months=incorporation_date_months,
            loan_size_vnd=loan_size_vnd,
            duration_months=duration_months,
            figures=figures,
            cic_score=cic,
        )
        try:
            return grade(inputs, p)
        except ValueError as exc:
            # `compute_derived` raises when profit <= 0 (D21). That is a real
            # answer about the applicant, not a bug, so it becomes a message
            # rather than a 500.
            message = str(exc)
            if "profit <= 0" in message:
                raise LiteGradingError(
                    "Your stated costs are equal to or greater than your "
                    "revenue, so an indicative rate cannot be calculated.",
                    code="COSTS_EXCEED_REVENUE",
                ) from exc
            raise

    low = run(CIC_BRACKET_LOW)
    high = run(CIC_BRACKET_HIGH)

    if low.interest_rate_pct is None or high.interest_rate_pct is None:
        # Should be unreachable: the bracket supplies cic_score, KYC is assumed,
        # and the series is 24 complete months. If it fires, an assumption above
        # has drifted and a silent fallback would hide it.
        raise LiteGradingError(
            f"The engine returned no rate (decisions: {low.decision}, "
            f"{high.decision}). Figures are insufficient to estimate a band.",
            code="NO_RATE",
        )

    assumptions = [
        f"CIC score is not known; bracketed across {CIC_BRACKET_LOW}-{CIC_BRACKET_HIGH}.",
        "Identity and AML checks are assumed to pass; they are verified for real later.",
        "Monthly revenue is modelled from the annual totals provided, not from filings.",
    ]
    if not _as_int(figures.get("revenue_best_month")):
        assumptions.append(
            "No best/worst month given, so revenue is modelled as flat — a real "
            "seasonal business may price differently."
        )
    if not _sector_is_reviewed():
        assumptions.append(
            "Industry risk data is a draft pending review, so this is provisional."
        )

    # A higher CIC is better, so `high` carries the lower rate. Ordered on the
    # values rather than assumed, so the band cannot come out inverted if the
    # sigmoid's direction is ever reconfigured.
    lo, hi = sorted((low.interest_rate_pct, high.interest_rate_pct))
    grade_lo, grade_hi = sorted(
        (low.final_grade or 0.0, high.final_grade or 0.0)
    )

    return LiteBand(
        rate_low_pct=lo,
        rate_high_pct=hi,
        grade_low=grade_lo,
        grade_high=grade_hi,
        decision_low=low.decision,
        decision_high=high.decision,
        engine_version=low.engine_version,
        params_version=low.params_version,
        sector_reference_version=str(
            _sector_table().get("sector_reference_version", "unknown")
        ),
        provisional=not _sector_is_reviewed(),
        assumptions=tuple(assumptions),
    )
