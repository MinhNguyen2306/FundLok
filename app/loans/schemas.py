from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class LoanApplicationCreate(BaseModel):
    business_id: UUID
    requested_amount: Decimal
    purpose: str | None = None
    repayment_preference: str | None = None


class LoanApplicationOut(BaseModel):
    id: UUID
    project_id: UUID
    requested_amount: Decimal
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


class LoanApplicationFiguresOut(LoanApplicationFiguresIn):
    """The stored figures, plus when they were last written.

    Returned so the wizard can repopulate itself when the applicant comes back
    to a draft rather than making them retype everything.
    """

    figures_updated_at: datetime | None = None
