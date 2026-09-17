from uuid import UUID

from pydantic import BaseModel


class ContractCreate(BaseModel):
    application_id: UUID
    score_run_id: UUID
    template_version: str | None = None


class ContractOut(BaseModel):
    id: UUID
    application_id: UUID | None
    score_run_id: UUID | None
    status: str
    target_amount: int
    funded_amount: int

    model_config = {"from_attributes": True}
