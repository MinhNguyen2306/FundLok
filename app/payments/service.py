"""Payments flow shim over the new double-entry ledger (app/ledger/).

HISTORY: this module used to write flat, single-entry `LedgerEntry` rows
directly (contract_id, type, amount, idempotency_key). The ledger foundation
migration (see docs/specs/ledger/ledger-foundation.md) turned `ledger_entries`
into the postings table of a double-entry system: `idempotency_key` moved to
`ledger_transactions`, and every row now requires a `ledger_transaction_id`,
`debit_account_id`, and `credit_account_id`. That schema change breaks this
module's old direct-insert pattern outright (NOT NULL violations, and the
`idempotency_key` column it queried no longer exists on `ledger_entries`).

This module is not owned by the ledger-foundation spec (out of scope, see
spec section 2: "Funding/disbursement/repayment/distribution endpoints and
flows... are specced per feature") and a real disbursement/repayment flow
spec is still TBD. This is a minimal compatibility adaptation only -- same
endpoints, same request/response contracts, same idempotency and
cross-contract-409 semantics as before -- rewired onto `app.ledger.service`
so the schema change doesn't silently break `/payments/*` (see the PR
description for the full rationale and the rounding caveat noted below).
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lending.models import Contract, Holding, LedgerEntry, Listing, LoanApplication, ProjectOwnership
from app.ledger.service import (
    LedgerLeg,
    get_or_create_account,
    resolve_custodial_account,
)
from app.ledger.models import LedgerTransaction


async def _resolve_borrower_user_id(db: AsyncSession, contract: Contract) -> UUID:
    """Contract -> LoanApplication -> Project -> the project's owning user.
    One-borrower-to-many-lenders per contract (spec Open Q#5), so the first
    ownership row is the borrower."""
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == contract.application_id))
    application = result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=400, detail="Contract has no associated loan application")

    result = await db.execute(
        select(ProjectOwnership).where(ProjectOwnership.project_id == application.project_id)
    )
    ownership = result.scalars().first()
    if ownership is None:
        raise HTTPException(status_code=400, detail="Project has no registered owner")
    return ownership.user_id


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
            select(LedgerTransaction).where(LedgerTransaction.idempotency_key == idempotency_key)
        )
        existing_txn = result.scalar_one_or_none()
        if existing_txn is not None:
            if existing_txn.contract_id != contract_id:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key already used for a different contract",
                )
            entry = await _first_entry_of_type(db, existing_txn.id, "DISBURSEMENT")
            return entry, False

    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
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

    custodial_account = await resolve_custodial_account(db, contract_id=contract_id)
    omnibus_cash = await get_or_create_account(
        db, account_type="OMNIBUS_CASH", custodial_account_id=custodial_account.id
    )
    borrower_user_id = await _resolve_borrower_user_id(db, contract)
    borrower_account = await get_or_create_account(
        db,
        account_type="BORROWER",
        custodial_account_id=custodial_account.id,
        owner_user_id=borrower_user_id,
        contract_id=contract_id,
    )

    transaction = await _post_transaction_with_service(
        db,
        event_type="DISBURSEMENT",
        legs=[
            LedgerLeg(
                debit_account_id=omnibus_cash.id,
                credit_account_id=borrower_account.id,
                amount=amount,
                type="DISBURSEMENT",
                contract_id=contract_id,
                reference=bank_account,
            )
        ],
        idempotency_key=idempotency_key,
        reference=bank_account,
        created_by=created_by,
    )
    entry = await _first_entry_of_type(db, transaction.id, "DISBURSEMENT")
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
            select(LedgerTransaction).where(LedgerTransaction.idempotency_key == idempotency_key)
        )
        existing_txn = result.scalar_one_or_none()
        if existing_txn is not None:
            if existing_txn.contract_id != contract_id:
                raise HTTPException(
                    status_code=409,
                    detail="Idempotency-Key already used for a different contract",
                )
            rep = await _first_entry_of_type(db, existing_txn.id, "REPAYMENT")
            dists = await _entries_of_type(db, existing_txn.id, "DISTRIBUTION")
            return rep, dists, False

    result = await db.execute(select(Contract).where(Contract.id == contract_id))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if contract.status != "ACTIVE_FUNDED":
        raise HTTPException(
            status_code=400,
            detail="Contract must be ACTIVE_FUNDED to record repayment",
        )

    result = await db.execute(select(Holding).where(Holding.contract_id == contract_id))
    holdings = result.scalars().all()
    total_principal = sum((h.principal for h in holdings), Decimal("0"))

    custodial_account = await resolve_custodial_account(db, contract_id=contract_id)
    omnibus_cash = await get_or_create_account(
        db, account_type="OMNIBUS_CASH", custodial_account_id=custodial_account.id
    )
    borrower_user_id = await _resolve_borrower_user_id(db, contract)
    borrower_account = await get_or_create_account(
        db,
        account_type="BORROWER",
        custodial_account_id=custodial_account.id,
        owner_user_id=borrower_user_id,
        contract_id=contract_id,
    )

    legs = [
        LedgerLeg(
            debit_account_id=borrower_account.id,
            credit_account_id=omnibus_cash.id,
            amount=amount,
            type="REPAYMENT",
            contract_id=contract_id,
            reference=reference,
        )
    ]

    # Distribution shares are principal-weighted, over integer VND (T1 --
    # no sub-unit currency exists to round to). Money is integer everywhere,
    # so this is Hamilton's largest-remainder apportionment done with exact
    # integer arithmetic (no Decimal division, no float, no quantize):
    # each holding's exact entitlement is (principal * amount / total_principal);
    # take the integer floor of that as its base share, then hand out the
    # `amount - sum(floors)` leftover VND one unit at a time to the holdings
    # with the largest fractional remainder (ties broken by holding id, for
    # determinism). This always sums to exactly `amount`, for any amount --
    # including amount as small as 1 VND split across many holdings, where
    # most floors are 0. post_transaction() rejects zero-amount legs, so a
    # holding whose final share is 0 is skipped entirely rather than posted
    # as an empty DISTRIBUTION leg.
    if total_principal > 0 and amount > 0:
        ordered_holdings = sorted(holdings, key=lambda h: h.id)
        total_principal_int = int(total_principal)
        amount_int = int(amount)

        shares: dict = {}
        remainders: dict = {}
        floor_sum = 0
        for holding in ordered_holdings:
            principal_int = int(holding.principal)
            numerator = principal_int * amount_int
            base_share, remainder = divmod(numerator, total_principal_int)
            shares[holding.id] = base_share
            remainders[holding.id] = remainder
            floor_sum += base_share

        leftover = amount_int - floor_sum
        # Largest fractional remainder first; deterministic tie-break by id.
        distribution_order = sorted(
            ordered_holdings,
            key=lambda h: (-remainders[h.id], str(h.id)),
        )
        for holding in distribution_order[:leftover]:
            shares[holding.id] += 1

        for holding in ordered_holdings:
            share = shares[holding.id]
            if share <= 0:
                continue
            lender_account = await get_or_create_account(
                db,
                account_type="LENDER",
                custodial_account_id=custodial_account.id,
                owner_user_id=holding.investor_id,
                contract_id=contract_id,
            )
            legs.append(
                LedgerLeg(
                    debit_account_id=omnibus_cash.id,
                    credit_account_id=lender_account.id,
                    amount=Decimal(share),
                    type="DISTRIBUTION",
                    contract_id=contract_id,
                    reference=f"repayment:investor:{holding.investor_id}",
                )
            )

    transaction = await _post_transaction_with_service(
        db,
        event_type="REPAYMENT_SPLIT" if len(legs) > 1 else "REPAYMENT",
        legs=legs,
        idempotency_key=idempotency_key,
        reference=reference,
        created_by=created_by,
    )
    rep = await _first_entry_of_type(db, transaction.id, "REPAYMENT")
    dists = await _entries_of_type(db, transaction.id, "DISTRIBUTION")
    return rep, dists, True


async def _post_transaction_with_service(db: AsyncSession, **kwargs) -> LedgerTransaction:
    from app.ledger.service import CrossContractTransactionError, LedgerImbalanceError, post_transaction

    try:
        return await post_transaction(db, **kwargs)
    except (LedgerImbalanceError, CrossContractTransactionError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


async def _first_entry_of_type(db: AsyncSession, ledger_transaction_id: UUID, type_: str) -> LedgerEntry:
    result = await db.execute(
        select(LedgerEntry).where(
            LedgerEntry.ledger_transaction_id == ledger_transaction_id,
            LedgerEntry.type == type_,
        )
    )
    return result.scalars().first()


async def _entries_of_type(db: AsyncSession, ledger_transaction_id: UUID, type_: str) -> list[LedgerEntry]:
    result = await db.execute(
        select(LedgerEntry).where(
            LedgerEntry.ledger_transaction_id == ledger_transaction_id,
            LedgerEntry.type == type_,
        )
    )
    return list(result.scalars().all())
