from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.banking import service
from app.banking.schemas import LinkAccountRequest, LinkedAccountOut
from app.core.database import get_db
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/banking", tags=["banking"])

authorized = require_roles(Role.SME, Role.INVESTOR)


@router.post("/accounts/link", response_model=LinkedAccountOut, status_code=201)
async def link_account(
    body: LinkAccountRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized),
):
    account = await service.link_account(
        db,
        user_id=current_user.id,
        account_type=body.account_type,
        account_number=body.account_number,
        provider=body.provider,
        display_name=body.display_name,
    )
    append_audit(
        db,
        entity_type="LINKED_ACCOUNT",
        entity_id=account.id,
        action="LINK",
        actor_id=current_user.id,
        after_state={"account_type": account.account_type, "provider": account.provider},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/accounts", response_model=list[LinkedAccountOut])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized),
):
    return await service.list_accounts(db, user_id=current_user.id)


@router.post("/accounts/{account_id}/unlink", response_model=LinkedAccountOut)
async def unlink_account(
    account_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(authorized),
):
    account = await service.unlink_account(db, user_id=current_user.id, account_id=account_id)
    append_audit(
        db,
        entity_type="LINKED_ACCOUNT",
        entity_id=account.id,
        action="UNLINK",
        actor_id=current_user.id,
        after_state={"status": account.status},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(account)
    return account
