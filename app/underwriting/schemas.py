from uuid import UUID

from pydantic import BaseModel
from decimal import Decimal


class ScoreRunCreate(BaseModel):
    application_id: UUID
    mode: str | None = None


class ScoreRunOut(BaseModel):
    id: UUID
    application_id: UUID
    status: str
    overall_score: Decimal | None
    risk_grade: str | None

    model_config = {"from_attributes": True}


class ScoreRunApproveOut(BaseModel):
    id: UUID
    locked_at: str | None
    status: str
