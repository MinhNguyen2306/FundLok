from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql import Select

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


async def _paginate(db: AsyncSession, stmt: Select, *, page: int, page_size: int, row_model, order_col) -> Page:
    """Apply offset pagination to a select() statement and wrap rows in a Page envelope."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one() or 0

    rows_stmt = stmt.order_by(order_col.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(rows_stmt)).scalars().all()

    total_pages = (total + page_size - 1) // page_size if page_size else 0
    return Page[row_model](
        items=[row_model.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


async def get_stats(db: AsyncSession) -> AdminStats:
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0

    users_by_role = dict(
        (await db.execute(select(User.role, func.count(User.id)).group_by(User.role))).all()
    )
    users_by_status = dict(
        (await db.execute(select(User.status, func.count(User.id)).group_by(User.status))).all()
    )
    projects_by_status = dict(
        (await db.execute(select(Project.status, func.count(Project.id)).group_by(Project.status))).all()
    )

    return AdminStats(
        total_users=total_users,
        total_projects=total_projects,
        users_by_role=users_by_role,
        users_by_status=users_by_status,
        projects_by_status=projects_by_status,
    )


async def list_users(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 14,
    search: str | None = None,
    status: str | None = None,
    role: str | None = None,
) -> Page:
    stmt = select(User)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(User.email.ilike(like), User.full_name.ilike(like)))
    if status:
        stmt = stmt.where(User.status == status)
    if role:
        stmt = stmt.where(User.role == role)
    return await _paginate(db, stmt, page=page, page_size=page_size, row_model=UserRow, order_col=User.created_at)


async def list_projects(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 14,
    search: str | None = None,
    status: str | None = None,
    industry: str | None = None,
) -> Page:
    stmt = select(Project)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Project.legal_name.ilike(like), Project.industry.ilike(like)))
    if status:
        stmt = stmt.where(Project.status == status)
    if industry:
        stmt = stmt.where(Project.industry.ilike(industry))
    return await _paginate(db, stmt, page=page, page_size=page_size, row_model=ProjectRow, order_col=Project.created_at)


async def get_overview(
    db: AsyncSession,
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
    stats = await get_stats(db)
    if mode == AdminMode.projects:
        table = await list_projects(
            db, page=page, page_size=page_size, search=search, status=status, industry=industry
        )
    else:
        table = await list_users(
            db, page=page, page_size=page_size, search=search, status=status, role=role
        )
    return AdminOverview(stats=stats, mode=mode, table=table)


async def list_audit_logs(
    db: AsyncSession,
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
    stmt = (
        select(AuditLog, actor, entity_user)
        .outerjoin(actor, actor.id == AuditLog.actor_id)
        .outerjoin(
            entity_user,
            and_(entity_user.id == AuditLog.entity_id, AuditLog.entity_type == "USER"),
        )
        .order_by(AuditLog.created_at.desc())
    )
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if created_after:
        stmt = stmt.where(AuditLog.created_at >= created_after)
    if created_before:
        stmt = stmt.where(AuditLog.created_at <= created_before)

    result = await db.execute(stmt.limit(limit))
    rows = result.all()
    out_list = []
    for log, actor_row, entity_user_row in rows:
        out = AuditLogOut.model_validate(log)
        out.actor = ActorOut.model_validate(actor_row) if actor_row else None
        out.entity_user = ActorOut.model_validate(entity_user_row) if entity_user_row else None
        out_list.append(out)
    return out_list
