from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.market.schemas import ListingCreate, ListingOut, OrderCreate, OrderOut
from app.market.service import create_listing, place_order
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/market", tags=["market"])

require_admin = require_roles(Role.ADMIN)
require_investor = require_roles(Role.INVESTOR)


@router.post("/listings", response_model=ListingOut, status_code=201)
async def post_listing(
    body: ListingCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    lst = await create_listing(db, body.contract_id, body.target_amount, body.min_ticket)
    append_audit(
        db,
        entity_type="LISTING",
        entity_id=lst.id,
        action="CREATE",
        actor_id=current_user.id,
        after_state={"contract_id": str(lst.contract_id), "status": lst.status},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return lst


@router.post("/listings/{listing_id}/orders", response_model=OrderOut, status_code=201)
async def post_order(
    listing_id: UUID,
    body: OrderCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_investor),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    order, is_new = await place_order(
        db,
        listing_id,
        current_user.id,
        body.amount,
        body.ack_risk_disclosure,
        idempotency_key,
    )
    if is_new:
        append_audit(
            db,
            entity_type="ORDER",
            entity_id=order.id,
            action="PLACE",
            actor_id=current_user.id,
            after_state={"amount": str(order.amount), "status": order.status},
            ip_address=request.client.host if request.client else None,
        )
    await db.commit()
    return order
