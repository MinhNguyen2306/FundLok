from pydantic import BaseModel
from datetime import date, datetime
from typing import Any
from uuid import UUID


class ProjectCreate(BaseModel):
    legal_name: str
    tax_id: str | None = None
    industry: str | None = None
    address: dict[str, Any] | None = None
    incorporation_date: date | None = None


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
