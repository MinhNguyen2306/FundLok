from uuid import UUID

from pydantic import BaseModel
from decimal import Decimal


class ContractCreate(BaseModel):
    application_id: UUID
    score_run_id: UUID
    template_version: str | None = None


class ContractOut(BaseModel):
    id: UUID
    application_id: UUID | None
    score_run_id: UUID | None
    status: str
    target_amount: Decimal
    funded_amount: Decimal

    model_config = {"from_attributes": True}
