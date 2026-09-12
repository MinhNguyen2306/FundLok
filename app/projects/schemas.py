from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.projects import engine_constraints
from app.uploads.schemas import LoanApplicationDocumentOut


class LoanApplicationCreateInline(BaseModel):
    requested_amount: Decimal
    # Loan term in months. Optional so an existing client that predates the
    # field keeps working; validated against the engine's
    # allowed_durations_months when present. Persisted as of migration
    # a4e91c2d7b58 — an application without it cannot be graded.
    duration_months: int | None = None
    purpose: str | None = None
    repayment_preference: str | None = None

    @field_validator("requested_amount")
    @classmethod
    def _amount_within_engine_bounds(cls, value: Decimal) -> Decimal:
        return engine_constraints.validate_loan_size(value)

    @field_validator("duration_months")
    @classmethod
    def _duration_is_allowed(cls, value: int | None) -> int | None:
        return engine_constraints.validate_duration_months(value)


class ProjectCreate(BaseModel):
    legal_name: str
    tax_id: str | None = None
    industry: str | None = None
    # Headcount as entered by the SME. `company_size` is derived from it below
    # rather than trusted from the client. Both persisted as of migration
    # a4e91c2d7b58 — see docs/specs/underwriting/grading-input-sources.md §3.3.
    employee_count: int | None = None
    company_size: str | None = None
    address: dict[str, Any] | None = None
    incorporation_date: date | None = None
    # Optional: the create-project form also collects loan info, so a DRAFT
    # loan application can be created in the same request.
    loan_application: LoanApplicationCreateInline | None = None

    @field_validator("industry")
    @classmethod
    def _industry_is_known_to_the_engine(cls, value: str | None) -> str | None:
        return engine_constraints.validate_industry(value)

    @field_validator("employee_count")
    @classmethod
    def _headcount_falls_in_a_band(cls, value: int | None) -> int | None:
        return engine_constraints.validate_employee_count(value)

    @model_validator(mode="after")
    def _derive_company_size(self) -> "ProjectCreate":
        """Recompute `company_size` from `employee_count`, overwriting whatever
        the client sent. The bands live in the params file, so the mapping is
        the server's to make (input-sources spec §6.3); a client-supplied band
        that contradicts the headcount would put a mis-scored application in
        the queue."""
        if self.employee_count is not None:
            object.__setattr__(
                self,
                "company_size",
                engine_constraints.company_size_for_headcount(self.employee_count),
            )
        return self


class ProjectOut(BaseModel):
    id: UUID
    legal_name: str
    tax_id: str | None
    industry: str | None
    employee_count: int | None = None
    company_size: str | None = None
    address: dict[str, Any] | None
    incorporation_date: date | None
    status: str
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ProjectLoanApplicationOut(BaseModel):
    id: UUID
    project_id: UUID
    requested_amount: Decimal
    duration_months: int | None = None
    purpose: str | None
    repayment_preference: str | None
    status: str
    submitted_at: datetime | None
    created_at: datetime | None
    documents: list[LoanApplicationDocumentOut] = []

    model_config = {"from_attributes": True}


class ProjectWithApplicationOut(ProjectOut):
    loan_application: ProjectLoanApplicationOut | None = None
