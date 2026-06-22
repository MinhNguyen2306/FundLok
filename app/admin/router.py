from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.admin import service
from app.admin.schemas import AdminMode, AdminOverview, AuditLogOut
from app.core.database import get_db
from app.users.models import Role, User
from app.utils.rbac import require_roles

router = APIRouter(prefix="/admin", tags=["admin"])

require_admin = require_roles(Role.ADMIN, Role.SYSTEM_ADMIN)


@router.get("/overview", response_model=AdminOverview)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    mode: AdminMode = Query(default=AdminMode.users),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=14, ge=1, le=100),
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    role: str | None = Query(default=None, description="users mode only"),
    industry: str | None = Query(default=None, description="projects mode only"),
):
    return service.get_overview(
        db,
        mode=mode,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        role=role,
        industry=industry,
    )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    entity_type: str | None = Query(default=None),
    entity_id: UUID | None = Query(default=None),
    actor_id: UUID | None = Query(default=None),
    created_after: datetime | None = Query(default=None),
    created_before: datetime | None = Query(default=None),
    limit: int = Query(default=100, le=500),
):
    return service.list_audit_logs(
        db,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
    )
