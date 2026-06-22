from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MaintenanceStatus(BaseModel):
    """Public maintenance status — safe to expose unauthenticated."""

    enabled: bool
    message: str | None = None


class MaintenanceState(MaintenanceStatus):
    """Full maintenance status, incl. audit fields (admin only)."""

    updated_at: datetime | None = None
    updated_by: UUID | None = None


class MaintenanceUpdate(BaseModel):
    enabled: bool
    message: str | None = None
