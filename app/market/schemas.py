from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListingCreate(BaseModel):
    contract_id: UUID
    target_amount: Decimal
    min_ticket: Decimal


class ListingOut(BaseModel):
    id: UUID
    contract_id: UUID
    target_amount: Decimal
    min_ticket: Decimal | None
    status: str
    funded_amount: Decimal

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: Decimal
    ack_risk_disclosure: bool = Field(default=False, alias="ackRiskDisclosure")


class OrderOut(BaseModel):
    id: UUID
    listing_id: UUID
    amount: Decimal
    status: str

    model_config = {"from_attributes": True}
