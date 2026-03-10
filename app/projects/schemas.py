from pydantic import BaseModel
from typing import Optional


class ProjectCreate(BaseModel):
    legal_name: str
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    address: Optional[dict] = None
    incorporation_date: Optional[str] = None  # ISO date string


class ProjectOut(BaseModel):
    id: str
    legal_name: str
    status: str
    # add more fields as needed