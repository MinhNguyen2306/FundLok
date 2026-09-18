from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentApprovalCreate(BaseModel):
    """Body for POST /lending/documents/{document_id}/approve (T15, GAP-1)."""

    rationale: str = Field(min_length=1, description="Why this document was approved -- goes into the audit log.")


class DocumentOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    purpose: str
    filename: str
    status: str
    verified_at: datetime | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
