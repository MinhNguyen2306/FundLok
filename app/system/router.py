from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.system import service
from app.system.schemas import MaintenanceState, MaintenanceStatus, MaintenanceUpdate
from app.users.models import Role, User
from app.utils.rbac import require_roles

router = APIRouter(prefix="/system", tags=["system"])

require_system_admin = require_roles(Role.SYSTEM_ADMIN)


@router.get("/maintenance", response_model=MaintenanceStatus)
async def get_maintenance(db: AsyncSession = Depends(get_db)):
    """Public: lets the frontend show a maintenance banner / gate login."""
    return await service.get_maintenance(db)


@router.put("/maintenance", response_model=MaintenanceState)
async def set_maintenance(
    body: MaintenanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_system_admin),
):
    return await service.set_maintenance(
        db, enabled=body.enabled, message=body.message, actor_id=current_user.id
    )
