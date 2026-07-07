from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LinkAccountRequest(BaseModel):
    account_type: str
    account_number: str
    provider: str | None = None
    display_name: str | None = None


class LinkedAccountOut(BaseModel):
    id: UUID
    account_type: str
    provider: str
    account_ref_masked: str
    display_name: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
