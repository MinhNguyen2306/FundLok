"""Ledger foundation service layer (app/ledger/).

Spec: docs/specs/ledger/ledger-foundation.md (ACCEPTED v1.0), section 4.
ADRs: docs/adr/002 (omnibus/custodial), docs/adr/003 (omnibus-first, escrow seam).

Internal service functions only -- no HTTP endpoints live here (per spec
section 2, "Out of Scope"). Callers (future funding/disbursement/repayment
flows) build HTTPException/status-code mapping on top of the exceptions
raised below. All functions are async / AsyncSession per CLAUDE.md.

Implementation note on "balanced legs" (spec section 3/6):
    Each `LedgerLeg` already carries both a debit_account_id and a
    credit_account_id for a single `amount` -- i.e. each leg is a complete,
    self-balancing transfer (this matches the `ledger_entries` row shape
    exactly: one row, one debit side, one credit side, one amount). Given
    that shape, a transaction's *total* debits always equal its *total*
    credits by construction, for any set of well-formed legs -- so a
    literal "sum of all debits == sum of all credits" check can never fail
    and would be a no-op.

    The invariant that can actually fail, and the one this service enforces
    as `LedgerImbalanceError`, is on any account used as a pass-through hub
    *within one transaction* -- the multi-leg repayment-split example from
    the spec (one REPAYMENT leg into OMNIBUS_CASH, then DISTRIBUTION +
    FEE legs paying it back out): OMNIBUS_CASH is touched by every leg, and
    the transaction is only "balanced" if what it received nets to zero
    against what it paid out. An account touched by exactly one leg is a
    genuine economic endpoint of the transaction (e.g. the LENDER account
    in a plain FUNDING transfer) and is exempt from the zero-net check.
"""
from __future__ import annotations

import dataclasses
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ledger.models import CustodialAccount, LedgerAccount, LedgerEntry, LedgerTransaction

VALID_LEDGER_ENTRY_TYPES = {
    "FUNDING",
    "DISBURSEMENT",
    "REPAYMENT",
    "DISTRIBUTION",
    "FEE",
    "PENALTY",
    "REFUND",
}


class LedgerError(Exception):
    """Base class for ledger service errors."""


class LedgerImbalanceError(LedgerError):
    """Raised when post_transaction's legs are malformed or a pass-through
    account does not net to zero within the transaction. Nothing is
    written when this is raised (see post_transaction)."""


class CrossContractTransactionError(LedgerError):
    """ADR-003 invariant: a single ledger_transaction must not move value
    between two different contracts' accounts. Nothing is written when
    this is raised."""


class CustodialAccountNotProvisioned(LedgerError):
    """Raised by resolve_custodial_account when a contract has no
    custodial account at all (escrow mode, not yet provisioned, and no
    PLATFORM account seeded to fall back on)."""


@dataclasses.dataclass(frozen=True)
class LedgerLeg:
    """One posting: `amount` moves from `debit_account_id` to
    `credit_account_id`. `type` is the economic label persisted on the
    resulting ledger_entries row. `contract_id` ring-fences this leg to one
    contract (ADR-003) -- ledger_entries.contract_id is NOT NULL, so every
    leg must declare one.
    """

    debit_account_id: UUID
    credit_account_id: UUID
    amount: Decimal
    type: str
    contract_id: UUID
    reference: Optional[str] = None


async def resolve_custodial_account(db: AsyncSession, *, contract_id: UUID) -> CustodialAccount:
    """OMNIBUS-FIRST SEAM (ADR-003): returns the contract's own CONTRACT-
    scoped custodial account if one has been provisioned (future escrow
    mode); otherwise falls back to the single PLATFORM account (omnibus,
    today). Callers MUST route through this function and never assume a
    global pool / cache a custodial account id across contracts.
    """
    result = await db.execute(
        select(CustodialAccount).where(
            CustodialAccount.scope == "CONTRACT",
            CustodialAccount.contract_id == contract_id,
        )
    )
    contract_account = result.scalar_one_or_none()
    if contract_account is not None:
        return contract_account

    result = await db.execute(select(CustodialAccount).where(CustodialAccount.scope == "PLATFORM"))
    platform_account = result.scalar_one_or_none()
    if platform_account is None:
        raise CustodialAccountNotProvisioned(
            f"No custodial account provisioned for contract {contract_id}: "
            "no CONTRACT-scoped account exists, and no PLATFORM account is seeded."
        )
    return platform_account


async def get_or_create_account(
    db: AsyncSession,
    *,
    account_type: str,
    custodial_account_id: UUID,
    owner_user_id: UUID | None = None,
    contract_id: UUID | None = None,
) -> LedgerAccount:
    """Fetch the (account_type, custodial_account_id, owner_user_id,
    contract_id) account, creating it on first use. This is the only
    construction path for LedgerAccount rows -- callers never build one
    directly, so the uniqueness key stays enforced in one place."""
    result = await db.execute(
        select(LedgerAccount).where(
            LedgerAccount.account_type == account_type,
            LedgerAccount.custodial_account_id == custodial_account_id,
            LedgerAccount.owner_user_id == owner_user_id,
            LedgerAccount.contract_id == contract_id,
        )
    )
    account = result.scalar_one_or_none()
    if account is not None:
        return account

    account = LedgerAccount(
        account_type=account_type,
        custodial_account_id=custodial_account_id,
        owner_user_id=owner_user_id,
        contract_id=contract_id,
    )
    db.add(account)
    await db.flush()
    return account


async def get_account_balance(db: AsyncSession, account_id: UUID) -> Decimal:
    """Balance(account) = SUM(credits) - SUM(debits), computed at read
    time from ledger_entries. There is no stored balance column anywhere
    to fall out of sync."""
    credit_result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(LedgerEntry.credit_account_id == account_id)
    )
    debit_result = await db.execute(
        select(func.coalesce(func.sum(LedgerEntry.amount), 0)).where(LedgerEntry.debit_account_id == account_id)
    )
    credits = Decimal(credit_result.scalar_one())
    debits = Decimal(debit_result.scalar_one())
    return credits - debits


async def post_transaction(
    db: AsyncSession,
    *,
    event_type: str,
    legs: list[LedgerLeg],
    idempotency_key: str | None,
    reference: str | None = None,
    created_by: UUID | None = None,
) -> LedgerTransaction:
    """Writes one balanced transaction + its legs atomically, or nothing.

    A single leg (e.g. a plain DISBURSEMENT: debit OMNIBUS_CASH, credit
    BORROWER) is a complete, self-balanced transaction on its own -- the
    list-of-legs shape exists to support multi-party events (e.g. one
    REPAYMENT split into N lender DISTRIBUTIONs + a FEE) as a single
    atomic, idempotent unit, not because every event needs >=2 rows.

    - Replays of an existing idempotency_key return the original
      transaction and write nothing new.
    - All validation happens before any row is added to the session, so a
      rejected call never leaves partial rows behind.
    """
    if not legs:
        raise LedgerImbalanceError("post_transaction requires at least one leg")

    for leg in legs:
        if leg.amount <= 0:
            raise LedgerImbalanceError(f"leg amount must be positive, got {leg.amount}")
        if leg.debit_account_id == leg.credit_account_id:
            raise LedgerImbalanceError("a leg's debit and credit account must differ")
        if leg.type not in VALID_LEDGER_ENTRY_TYPES:
            raise LedgerImbalanceError(f"invalid ledger entry type: {leg.type!r}")

    if idempotency_key:
        result = await db.execute(
            select(LedgerTransaction).where(LedgerTransaction.idempotency_key == idempotency_key)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing

    # Cross-contract ring-fencing (ADR-003) is checked *before* the
    # arithmetic balance check below: it's a structural/domain violation
    # (don't co-mingle two contracts' money in one event) independent of
    # whether the amounts happen to net out, and checking it first gives a
    # clearer error when both would otherwise fire -- e.g. two legs against
    # the same shared OMNIBUS_CASH account for two different contracts will
    # also look like an unbalanced pass-through, but the real problem is
    # the cross-contract mixing, not the arithmetic.
    account_ids = {a for leg in legs for a in (leg.debit_account_id, leg.credit_account_id)}
    account_rows: dict[UUID, LedgerAccount] = {}
    if account_ids:
        result = await db.execute(select(LedgerAccount).where(LedgerAccount.id.in_(account_ids)))
        account_rows = {a.id: a for a in result.scalars().all()}

    contract_ids: set[UUID] = set()
    for leg in legs:
        contract_ids.add(leg.contract_id)
        for account_id in (leg.debit_account_id, leg.credit_account_id):
            account = account_rows.get(account_id)
            if account is not None and account.contract_id is not None:
                contract_ids.add(account.contract_id)

    if len(contract_ids) > 1:
        raise CrossContractTransactionError(
            f"transaction legs span multiple contracts: {sorted(str(c) for c in contract_ids)}"
        )
    transaction_contract_id = next(iter(contract_ids))

    # Pass-through balance check: any account touched by more than one leg
    # in this transaction must net to zero (see module docstring).
    net: dict[UUID, Decimal] = {}
    touches: dict[UUID, int] = {}
    for leg in legs:
        net[leg.debit_account_id] = net.get(leg.debit_account_id, Decimal("0")) - leg.amount
        net[leg.credit_account_id] = net.get(leg.credit_account_id, Decimal("0")) + leg.amount
        touches[leg.debit_account_id] = touches.get(leg.debit_account_id, 0) + 1
        touches[leg.credit_account_id] = touches.get(leg.credit_account_id, 0) + 1

    for account_id, count in touches.items():
        if count > 1 and net[account_id] != 0:
            raise LedgerImbalanceError(
                f"account {account_id} is used as a pass-through in this transaction "
                f"but does not net to zero (net={net[account_id]})"
            )

    transaction = LedgerTransaction(
        event_type=event_type,
        contract_id=transaction_contract_id,
        idempotency_key=idempotency_key,
        reference=reference,
        created_by=created_by,
    )
    db.add(transaction)
    await db.flush()

    for leg in legs:
        db.add(
            LedgerEntry(
                contract_id=leg.contract_id,
                ledger_transaction_id=transaction.id,
                debit_account_id=leg.debit_account_id,
                credit_account_id=leg.credit_account_id,
                type=leg.type,
                amount=leg.amount,
                reference=leg.reference or reference,
                created_by=created_by,
            )
        )
    await db.flush()
    await db.refresh(transaction)
    return transaction
