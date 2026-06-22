from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.system import service
from app.system.schemas import MaintenanceState, MaintenanceStatus, MaintenanceUpdate
from app.users.models import Role, User
from app.utils.rbac import require_roles

router = APIRouter(prefix="/system", tags=["system"])

require_system_admin = require_roles(Role.SYSTEM_ADMIN)


@router.get("/maintenance", response_model=MaintenanceStatus)
def get_maintenance(db: Session = Depends(get_db)):
    """Public: lets the frontend show a maintenance banner / gate login."""
    return service.get_maintenance(db)


@router.put("/maintenance", response_model=MaintenanceState)
def set_maintenance(
    body: MaintenanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_system_admin),
):
    return service.set_maintenance(
        db, enabled=body.enabled, message=body.message, actor_id=current_user.id
    )
