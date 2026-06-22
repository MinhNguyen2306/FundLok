from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

T = TypeVar("T")


class AdminMode(str, Enum):
    """Which table the overview screen should load alongside the stats."""

    users = "users"
    projects = "projects"


class Page(BaseModel, Generic[T]):
    """Generic paginated envelope shared by every admin list endpoint."""

    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminStats(BaseModel):
    total_users: int
    total_projects: int
    users_by_role: dict[str, int]
    users_by_status: dict[str, int]
    projects_by_status: dict[str, int]


class UserRow(BaseModel):
    id: UUID
    email: str
    full_name: str | None
    role: str
    status: str
    email_verified: bool
    created_at: datetime | None

    model_config = {"from_attributes": True}


class ProjectRow(BaseModel):
    id: UUID
    legal_name: str
    tax_id: str | None
    industry: str | None
    status: str
    created_at: datetime | None

    model_config = {"from_attributes": True}


class AdminOverview(BaseModel):
    """BFF payload: the whole admin overview screen in one response."""

    stats: AdminStats
    mode: AdminMode
    table: Page[UserRow] | Page[ProjectRow]


class ActorOut(BaseModel):
    """Minimal user info attached to an audit log (actor / USER entity)."""

    id: UUID
    full_name: str | None
    email: str | None

    model_config = {"from_attributes": True}


class AuditLogOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID | None
    action: str
    actor_id: UUID | None
    actor: ActorOut | None = None
    entity_user: ActorOut | None = None  # populated only when entity_type == 'USER'
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    ip_address: str | None
    created_at: datetime | None

    model_config = {"from_attributes": True}
