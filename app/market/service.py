from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.lending.kyc import project_has_verified_kyc
from app.lending.models import Contract, Holding, Listing, LoanApplication, Order


def _dec(value: object) -> Decimal:
    """Coerce ORM / JSON numerics to Decimal (avoids Decimal ± float TypeError)."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, int) and not isinstance(value, bool):
        return Decimal(value)
    return Decimal(str(value))


def _recompute_holding_shares(db: Session, contract_id: UUID) -> None:
    hs = db.query(Holding).filter(Holding.contract_id == contract_id).all()
    total = sum((_dec(h.principal) for h in hs), Decimal("0"))
    if total <= 0:
        return
    for h in hs:
        p = _dec(h.principal)
        h.share_ratio = (p / total).quantize(Decimal("0.00000001"))
        db.add(h)


def create_listing(db: Session, contract_id: UUID, target_amount: Decimal, min_ticket: Decimal) -> Listing:
    c = db.query(Contract).filter(Contract.id == contract_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    if c.status != "ACTIVE_PENDING_FUNDING":
        raise HTTPException(
            status_code=400,
            detail="Contract must be ACTIVE_PENDING_FUNDING to list",
        )
    app = db.query(LoanApplication).filter(LoanApplication.id == c.application_id).first()
    if not app:
        raise HTTPException(status_code=400, detail="Contract has no application")
    if not project_has_verified_kyc(db, app.project_id):
        raise HTTPException(
            status_code=400,
            detail="Project must have all KYC documents APPROVED before listing",
        )
    existing = db.query(Listing).filter(Listing.contract_id == contract_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Listing already exists for this contract")
    if min_ticket <= 0:
        raise HTTPException(status_code=400, detail="min_ticket must be positive")
    now = datetime.now(timezone.utc)
    lst = Listing(
        contract_id=contract_id,
        target_amount=target_amount,
        min_ticket=min_ticket,
        status="OPEN",
        funded_amount=Decimal("0"),
        open_at=now,
    )
    db.add(lst)
    db.flush()
    db.refresh(lst)
    return lst


def place_order(
    db: Session,
    listing_id: UUID,
    investor_id: UUID,
    amount: Decimal,
    ack_risk_disclosure: bool,
    idempotency_key: str | None,
) -> tuple[Order, bool]:
    if not ack_risk_disclosure:
        raise HTTPException(status_code=400, detail="Risk disclosure must be acknowledged")
    if idempotency_key:
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
        if existing:
            if existing.listing_id != listing_id:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key already used for a different listing",
                )
            return existing, False

    lst = db.query(Listing).filter(Listing.id == listing_id).first()
    if not lst:
        raise HTTPException(status_code=404, detail="Listing not found")
    if lst.status != "OPEN":
        raise HTTPException(status_code=400, detail="Listing is not open for funding")

    amount = _dec(amount)
    target_amt = _dec(lst.target_amount)
    funded_amt = _dec(lst.funded_amount)
    min_ticket = _dec(lst.min_ticket) if lst.min_ticket is not None else None

    if min_ticket is not None and amount < min_ticket:
        raise HTTPException(status_code=400, detail="Amount below min_ticket")
    remaining = target_amt - funded_amt
    if amount > remaining:
        raise HTTPException(status_code=400, detail="Amount exceeds remaining capacity")

    now = datetime.now(timezone.utc)
    order = Order(
        listing_id=listing_id,
        investor_id=investor_id,
        amount=amount,
        status="FILLED",
        payment_confirmed_at=now,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    db.flush()

    new_listing_funded = funded_amt + amount
    lst.funded_amount = new_listing_funded
    c = db.query(Contract).filter(Contract.id == lst.contract_id).first()
    if c:
        c.funded_amount = _dec(c.funded_amount) + amount

    holding = (
        db.query(Holding)
        .filter(Holding.contract_id == lst.contract_id, Holding.investor_id == investor_id)
        .first()
    )
    if holding:
        holding.principal = _dec(holding.principal) + amount
        holding.order_id = order.id
    else:
        holding = Holding(
            contract_id=lst.contract_id,
            investor_id=investor_id,
            order_id=order.id,
            principal=amount,
        )
        db.add(holding)

    if new_listing_funded >= target_amt:
        lst.status = "FUNDED"
        lst.close_at = now
        if c:
            c.status = "ACTIVE_FUNDED"

    db.add(lst)
    if c:
        db.add(c)
    db.flush()
    _recompute_holding_shares(db, lst.contract_id)
    db.flush()
    db.refresh(order)
    return order, True
