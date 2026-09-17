from uuid import UUID

from pydantic import BaseModel


class LoanApplicationCreate(BaseModel):
    business_id: UUID
    requested_amount: int
    purpose: str | None = None
    repayment_preference: str | None = None


class LoanApplicationOut(BaseModel):
    id: UUID
    project_id: UUID
    requested_amount: int
    purpose: str | None
    repayment_preference: str | None
    status: str

    model_config = {"from_attributes": True}
