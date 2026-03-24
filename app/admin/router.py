from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.admin.schemas import AuditLogOut
from app.core.database import get_db
from app.lending.models import AuditLog
from app.users.models import Role, User
from app.utils.rbac import require_roles

router = APIRouter(prefix="/admin", tags=["admin"])

require_admin = require_roles(Role.ADMIN)


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
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        q = q.filter(AuditLog.entity_id == entity_id)
    if actor_id:
        q = q.filter(AuditLog.actor_id == actor_id)
    if created_after:
        q = q.filter(AuditLog.created_at >= created_after)
    if created_before:
        q = q.filter(AuditLog.created_at <= created_before)
    return q.limit(limit).all()
