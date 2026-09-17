from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListingCreate(BaseModel):
    contract_id: UUID
    target_amount: int
    min_ticket: int


class ListingOut(BaseModel):
    id: UUID
    contract_id: UUID
    target_amount: int
    min_ticket: int | None
    status: str
    funded_amount: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    amount: int
    ack_risk_disclosure: bool = Field(default=False, alias="ackRiskDisclosure")


class OrderOut(BaseModel):
    id: UUID
    listing_id: UUID
    amount: int
    status: str

    model_config = {"from_attributes": True}
