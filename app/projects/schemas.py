from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.uploads.schemas import LoanApplicationDocumentOut


class LoanApplicationCreateInline(BaseModel):
    requested_amount: Decimal
    purpose: str | None = None
    repayment_preference: str | None = None


class ProjectCreate(BaseModel):
    legal_name: str
    tax_id: str | None = None
    industry: str | None = None
    address: dict[str, Any] | None = None
    incorporation_date: date | None = None
    # Optional: the create-project form also collects loan info, so a DRAFT
    # loan application can be created in the same request.
    loan_application: LoanApplicationCreateInline | None = None


class ProjectOut(BaseModel):
    id: UUID
    legal_name: str
    tax_id: str | None
    industry: str | None
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
    purpose: str | None
    repayment_preference: str | None
    status: str
    submitted_at: datetime | None
    created_at: datetime | None
    documents: list[LoanApplicationDocumentOut] = []

    model_config = {"from_attributes": True}


class ProjectWithApplicationOut(ProjectOut):
    loan_application: ProjectLoanApplicationOut | None = None
