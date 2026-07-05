from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.payments.schemas import DisbursementCreate, DisbursementOut, RepaymentCreate, RepaymentOut, DistributionOut
from app.payments.service import record_disbursement, record_repayment
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/payments", tags=["payments"])

require_admin = require_roles(Role.ADMIN)


@router.post("/disbursements", response_model=DisbursementOut, status_code=201)
async def post_disbursement(
    body: DisbursementCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    entry, is_new = await record_disbursement(
        db,
        contract_id=body.contract_id,
        bank_account=body.bank_account,
        amount=body.amount,
        idempotency_key=idempotency_key,
        created_by=current_user.id,
    )
    if is_new:
        append_audit(
            db,
            entity_type="LEDGER",
            entity_id=entry.id,
            action="DISBURSEMENT",
            actor_id=current_user.id,
            after_state={"amount": str(body.amount), "contract_id": str(body.contract_id)},
            ip_address=request.client.host if request.client else None,
        )
    await db.commit()
    return DisbursementOut(disbursement_id=entry.id, status="RECORDED")


@router.post("/repayments", response_model=RepaymentOut, status_code=201)
async def post_repayment(
    body: RepaymentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    rep, dists, is_new = await record_repayment(
        db,
        contract_id=body.contract_id,
        amount=body.amount,
        paid_at=body.paid_at,
        reference=body.reference,
        idempotency_key=idempotency_key,
        created_by=current_user.id,
    )
    if is_new:
        append_audit(
            db,
            entity_type="LEDGER",
            entity_id=rep.id,
            action="REPAYMENT",
            actor_id=current_user.id,
            after_state={"amount": str(body.amount), "distributions": len(dists)},
            ip_address=request.client.host if request.client else None,
        )
    await db.commit()
    balances = [DistributionOut(ledger_entry_id=d.id, amount=d.amount) for d in dists]
    return RepaymentOut(repayment_id=rep.id, balances=balances)
