from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.contracts.schemas import ContractCreate, ContractOut
from app.contracts.service import create_contract
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/contracts", tags=["contracts"])

require_admin = require_roles(Role.ADMIN)


@router.post("/", response_model=ContractOut, status_code=201)
async def post_contract(
    body: ContractCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    c = await create_contract(db, body)
    append_audit(
        db,
        entity_type="CONTRACT",
        entity_id=c.id,
        action="CREATE",
        actor_id=current_user.id,
        after_state={"status": c.status, "target_amount": str(c.target_amount)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return c
