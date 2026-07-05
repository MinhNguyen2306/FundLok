from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lending.models import Contract, Holding, LedgerEntry, Listing


async def record_disbursement(
    db: AsyncSession,
    *,
    contract_id: UUID,
    bank_account: str,
    amount: Decimal,
    idempotency_key: str | None,
    created_by: UUID,
) -> tuple[LedgerEntry, bool]:
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if idempotency_key:
        result = await db.execute(
            select(LedgerEntry).where(LedgerEntry.idempotency_key == idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.contract_id != contract_id:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key already used for a different contract",
                )
            return existing, False

    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    result = await db.execute(select(Listing).where(Listing.contract_id == contract_id))
    lst = result.scalar_one_or_none()
    if not lst or lst.status != "FUNDED":
        raise HTTPException(
            status_code=400,
            detail="Listing must be FUNDED before disbursement",
        )
    if lst.funded_amount < lst.target_amount:
        raise HTTPException(status_code=400, detail="Listing funding threshold not met")

    entry = LedgerEntry(
        contract_id=contract_id,
        type="DISBURSEMENT",
        amount=amount,
        reference=bank_account,
        created_by=created_by,
        idempotency_key=idempotency_key,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry, True


async def record_repayment(
    db: AsyncSession,
    *,
    contract_id: UUID,
    amount: Decimal,
    paid_at: datetime,
    reference: str | None,
    idempotency_key: str | None,
    created_by: UUID,
) -> tuple[LedgerEntry, list[LedgerEntry], bool]:
    if amount < 0:
        raise HTTPException(status_code=400, detail="Amount must be non-negative")

    if idempotency_key:
        result = await db.execute(
            select(LedgerEntry).where(
                LedgerEntry.idempotency_key == idempotency_key,
                LedgerEntry.type == "REPAYMENT",
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if existing.contract_id != contract_id:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key already used for a different contract",
                )
            pattern = f"repayment:{existing.id}:%"
            result = await db.execute(
                select(LedgerEntry).where(
                    LedgerEntry.contract_id == contract_id,
                    LedgerEntry.type == "DISTRIBUTION",
                    LedgerEntry.reference.like(pattern),
                )
            )
            dists = result.scalars().all()
            return existing, dists, False

    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Contract not found")
    if c.status != "ACTIVE_FUNDED":
        raise HTTPException(
            status_code=400,
            detail="Contract must be ACTIVE_FUNDED to record repayment",
        )

    rep = LedgerEntry(
        contract_id=contract_id,
        type="REPAYMENT",
        amount=amount,
        reference=reference,
        occurred_at=paid_at,
        created_by=created_by,
        idempotency_key=idempotency_key,
    )
    db.add(rep)
    await db.flush()

    result = await db.execute(select(Holding).where(Holding.contract_id == contract_id))
    holdings = result.scalars().all()
    total_principal = sum((h.principal for h in holdings), Decimal("0"))
    distributions: list[LedgerEntry] = []
    if total_principal > 0 and amount > 0:
        for h in holdings:
            share = (h.principal / total_principal) * amount
            dist = LedgerEntry(
                contract_id=contract_id,
                type="DISTRIBUTION",
                amount=share.quantize(Decimal("0.01")),
                reference=f"repayment:{rep.id}:investor:{h.investor_id}",
                occurred_at=paid_at,
                created_by=created_by,
            )
            db.add(dist)
            distributions.append(dist)
    await db.flush()
    await db.refresh(rep)
    return rep, distributions, True
