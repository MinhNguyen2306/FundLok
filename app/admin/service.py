from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Query, Session, aliased

from app.admin.schemas import (
    ActorOut,
    AdminMode,
    AdminOverview,
    AdminStats,
    AuditLogOut,
    Page,
    ProjectRow,
    UserRow,
)
from app.lending.models import AuditLog, Project
from app.users.models import User


def _paginate(q: Query, *, page: int, page_size: int, row_model, order_col) -> Page:
    """Apply offset pagination to a query and wrap rows in a Page envelope."""
    total = q.order_by(None).count()
    rows = (
        q.order_by(order_col.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return Page[row_model](
        items=[row_model.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


def get_stats(db: Session) -> AdminStats:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_projects = db.query(func.count(Project.id)).scalar() or 0

    users_by_role = dict(
        db.query(User.role, func.count(User.id)).group_by(User.role).all()
    )
    users_by_status = dict(
        db.query(User.status, func.count(User.id)).group_by(User.status).all()
    )
    projects_by_status = dict(
        db.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
    )

    return AdminStats(
        total_users=total_users,
        total_projects=total_projects,
        users_by_role=users_by_role,
        users_by_status=users_by_status,
        projects_by_status=projects_by_status,
    )


def list_users(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 14,
    search: str | None = None,
    status: str | None = None,
    role: str | None = None,
) -> Page:
    q = db.query(User)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(User.email.ilike(like), User.full_name.ilike(like)))
    if status:
        q = q.filter(User.status == status)
    if role:
        q = q.filter(User.role == role)
    return _paginate(q, page=page, page_size=page_size, row_model=UserRow, order_col=User.created_at)


def list_projects(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 14,
    search: str | None = None,
    status: str | None = None,
    industry: str | None = None,
) -> Page:
    q = db.query(Project)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Project.legal_name.ilike(like), Project.industry.ilike(like)))
    if status:
        q = q.filter(Project.status == status)
    if industry:
        q = q.filter(Project.industry.ilike(industry))
    return _paginate(q, page=page, page_size=page_size, row_model=ProjectRow, order_col=Project.created_at)


def get_overview(
    db: Session,
    *,
    mode: AdminMode = AdminMode.users,
    page: int = 1,
    page_size: int = 14,
    search: str | None = None,
    status: str | None = None,
    role: str | None = None,
    industry: str | None = None,
) -> AdminOverview:
    """One-shot BFF payload: stats + whichever table the frontend asked for."""
    stats = get_stats(db)
    if mode == AdminMode.projects:
        table = list_projects(
            db, page=page, page_size=page_size, search=search, status=status, industry=industry
        )
    else:
        table = list_users(
            db, page=page, page_size=page_size, search=search, status=status, role=role
        )
    return AdminOverview(stats=stats, mode=mode, table=table)


def list_audit_logs(
    db: Session,
    *,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    actor_id: UUID | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    limit: int = 100,
) -> list[AuditLogOut]:
    # Resolve the two UUID columns to user info in a single query (no N+1):
    #   - actor   -> the user who performed the action
    #   - entity_user -> the subject user, only when entity_type == 'USER'
    actor = aliased(User)
    entity_user = aliased(User)
    q = (
        db.query(AuditLog, actor, entity_user)
        .outerjoin(actor, actor.id == AuditLog.actor_id)
        .outerjoin(
            entity_user,
            and_(entity_user.id == AuditLog.entity_id, AuditLog.entity_type == "USER"),
        )
        .order_by(AuditLog.created_at.desc())
    )
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

    rows = q.limit(limit).all()
    result = []
    for log, actor_row, entity_user_row in rows:
        out = AuditLogOut.model_validate(log)
        out.actor = ActorOut.model_validate(actor_row) if actor_row else None
        out.entity_user = ActorOut.model_validate(entity_user_row) if entity_user_row else None
        result.append(out)
    return result
