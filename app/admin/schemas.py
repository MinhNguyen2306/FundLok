from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class AuditLogOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID | None
    action: str
    actor_id: UUID | None
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
