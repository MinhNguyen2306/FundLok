from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.projects import engine_constraints


class LoanApplicationCreate(BaseModel):
    business_id: UUID
    requested_amount: Decimal
    # Validated against the engine's allowed_durations_months, like the inline
    # create on POST /projects: a term the engine does not grade is unscoreable,
    # and this is the last point at which the applicant still has the field in
    # front of them.
    #
    # `requested_amount` is deliberately NOT bounds-checked here, unlike on the
    # inline path. This route is not the applicant-facing one -- the wizard
    # creates its application through POST /projects, where the check already
    # runs -- and applying it here would reject the small synthetic amounts that
    # the order, ledger and idempotency suites use to test unrelated things. An
    # out-of-bounds amount that reaches the engine surfaces as a 409 from the
    # indicative-rate endpoint rather than a 500.
    duration_months: int | None = None
    purpose: str | None = None
    repayment_preference: str | None = None

    @field_validator("duration_months")
    @classmethod
    def _duration_is_allowed(cls, value: int | None) -> int | None:
        return engine_constraints.validate_duration_months(value)


class LoanApplicationOut(BaseModel):
    id: UUID
    project_id: UUID
    requested_amount: Decimal
    duration_months: int | None = None
    purpose: str | None
    repayment_preference: str | None
    status: str

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Lite grading figures
#
# The applicant types these instead of uploading the VAT and annual-report
# bundles. See the LoanApplication.self_reported_figures comment for why they
# are stored as JSONB; this model is the contract that guards that column.
#
# Every bound here is duplicated in the browser
# (Frontendfundlok/app/dashboard/_components/loan-application/lite-grading-fields.ts)
# so the applicant gets an instant error, but the browser copy is a convenience
# only -- a client can post anything, so these figures are validated again here
# before they reach underwriting.
# --------------------------------------------------------------------------- #

# A ceiling far above any plausible SME turnover. Its job is to catch a
# mistyped extra digit -- without it, a slipped keystroke grades a corner shop
# as a conglomerate, and the applicant never sees why their band was wrong.
VND_MAX = 1_000_000_000_000  # 1 trillion đồng

# VND amounts are whole đồng: the currency has no sub-unit, so a fractional
# figure is always an input error rather than precision.
VndAmount = Field(gt=0, le=VND_MAX)
OptionalVndAmount = Field(default=None, gt=0, le=VND_MAX)
OptionalPercent = Field(default=None, ge=0, le=100)


class LoanApplicationFiguresIn(BaseModel):
    """What the SME states on the revenue and costs steps.

    `None` on an optional field means "left blank", which is deliberately NOT
    the same as 0: 0 is a real answer the engine scores (a company with no
    customer concentration), and collapsing the two would silently invent data.
    """

    # --- Required: the engine cannot produce a band without these -----------
    revenue_last_12m: int = VndAmount
    revenue_prior_12m: int = VndAmount
    cogs_y1: int = VndAmount
    fixed_cost_y1: int = VndAmount
    variable_cost_excl_cogs_y1: int = VndAmount

    # --- Optional: they sharpen the band rather than enable it --------------
    revenue_best_month: int | None = OptionalVndAmount
    revenue_worst_month: int | None = OptionalVndAmount
    owner_withdrawal_pct: float | None = OptionalPercent
    conc_top1_pct: float | None = OptionalPercent
    conc_top3_pct: float | None = OptionalPercent

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def _check_internally_consistent(self) -> "LoanApplicationFiguresIn":
        """Reject figure sets that cannot describe a real company.

        Each of these passes field-level validation while still being
        impossible, and every one of them is a plausible typo rather than a
        hypothetical. Catching them here means the applicant is told which
        number to fix, instead of underwriting scoring a contradiction.
        """
        best = self.revenue_best_month
        worst = self.revenue_worst_month

        if best is not None and worst is not None and worst > best:
            raise ValueError(
                "revenue_worst_month cannot exceed revenue_best_month"
            )

        # A single month cannot out-earn the year that contains it.
        for name, value in (
            ("revenue_best_month", best),
            ("revenue_worst_month", worst),
        ):
            if value is not None and value > self.revenue_last_12m:
                raise ValueError(f"{name} cannot exceed revenue_last_12m")

        top1 = self.conc_top1_pct
        top3 = self.conc_top3_pct
        if top1 is not None and top3 is not None and top1 > top3:
            # The top 3 include the top 1 by definition.
            raise ValueError("conc_top1_pct cannot exceed conc_top3_pct")

        return self


class IndicativeRateOut(BaseModel):
    """An indicative interest band for an application, never an offer.

    Mirrors `app.loans.lite_grading.LiteBand` field for field. The shape is a
    RANGE by construction: the applicant's CIC score is unknown before KYC, so
    the engine is run at both ends of the range it was calibrated against and
    the two rates bracket the answer. There is deliberately no single-figure
    variant of this response — a point estimate would read as a quote.

    `assumptions` is not decoration. Each entry names a thing the band took on
    faith (bracketed CIC, assumed AML pass, revenue modelled from annual
    totals), and the UI is required to show them alongside the numbers.
    """

    rate_low_pct: float
    rate_high_pct: float
    grade_low: float
    grade_high: float
    decision_low: str
    decision_high: str

    # Stamped so a band a user was shown can be reconstructed later, per the
    # handbook's rule that anything shown to a user is versioned.
    engine_version: str
    params_version: str
    sector_reference_version: str

    # True while the sector reference table is still DRAFT_UNREVIEWED. Sector
    # drives 36% of the spread, so the table's own instruction is that callers
    # surface results as provisional until the CEO signs it off.
    provisional: bool
    assumptions: list[str]


class LoanApplicationFiguresOut(LoanApplicationFiguresIn):
    """The stored figures, plus when they were last written.

    Returned so the wizard can repopulate itself when the applicant comes back
    to a draft rather than making them retype everything.
    """

    figures_updated_at: datetime | None = None
