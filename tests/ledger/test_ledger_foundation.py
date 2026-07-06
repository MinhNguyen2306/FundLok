"""Ledger double-entry foundation -- spec acceptance criteria (section 8).

Spec: docs/specs/ledger/ledger-foundation.md (ACCEPTED v1.0)
ADRs: docs/adr/002-omnibus-brankas-architecture.md,
      docs/adr/003-omnibus-first-escrow-compatible-ledger.md

These exercise app/ledger/service.py directly against a real AsyncSession
(the `db_session` fixture) -- this spec defines internal service functions,
not HTTP endpoints (see spec section 2), so there is no `client` involved
here. `funded_contract` (existing conftest fixture) gets us a real
contract + investor through the actual API, which we then post ledger
transactions against.
"""
import uuid
from decimal import Decimal

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.ledger.models import CustodialAccount, LedgerAccount, LedgerEntry, LedgerTransaction
from app.ledger.service import (
    CrossContractTransactionError,
    LedgerImbalanceError,
    LedgerLeg,
    get_account_balance,
    get_or_create_account,
    post_transaction,
    resolve_custodial_account,
)


async def _setup_accounts(db_session, setup):
    """Resolve the platform custodial account and the OMNIBUS_CASH /
    BORROWER / LENDER accounts for one funded_contract() setup."""
    contract_id = uuid.UUID(setup["contract"]["id"])
    custodial = await resolve_custodial_account(db_session, contract_id=contract_id)
    omnibus = await get_or_create_account(db_session, account_type="OMNIBUS_CASH", custodial_account_id=custodial.id)
    borrower = await get_or_create_account(
        db_session,
        account_type="BORROWER",
        custodial_account_id=custodial.id,
        owner_user_id=uuid.UUID(setup["sme"]["id"]),
        contract_id=contract_id,
    )
    lender = await get_or_create_account(
        db_session,
        account_type="LENDER",
        custodial_account_id=custodial.id,
        owner_user_id=uuid.UUID(setup["investor"]["id"]),
        contract_id=contract_id,
    )
    return {"contract_id": contract_id, "custodial": custodial, "omnibus": omnibus, "borrower": borrower, "lender": lender}


async def test_post_transaction_writes_balanced_legs_atomically(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)

    txn = await post_transaction(
        db_session,
        event_type="FUNDING_THEN_DISBURSEMENT",
        legs=[
            LedgerLeg(
                debit_account_id=accts["lender"].id,
                credit_account_id=accts["omnibus"].id,
                amount=Decimal("500.00"),
                type="FUNDING",
                contract_id=accts["contract_id"],
            ),
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=accts["borrower"].id,
                amount=Decimal("500.00"),
                type="DISBURSEMENT",
                contract_id=accts["contract_id"],
            ),
        ],
        idempotency_key=f"atomic-2leg-{uuid.uuid4().hex}",
    )
    await db_session.commit()

    assert txn.id is not None
    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.ledger_transaction_id == txn.id))
    entries = result.scalars().all()
    assert len(entries) == 2
    assert {e.type for e in entries} == {"FUNDING", "DISBURSEMENT"}


async def test_post_transaction_rejects_unbalanced_legs(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)

    # OMNIBUS_CASH receives 500 (FUNDING) but only 300 is paid back out
    # (DISBURSEMENT) -- OMNIBUS_CASH nets to +200 within this transaction,
    # instead of 0. Nothing should be written.
    with pytest.raises(LedgerImbalanceError):
        await post_transaction(
            db_session,
            event_type="BROKEN",
            legs=[
                LedgerLeg(
                    debit_account_id=accts["lender"].id,
                    credit_account_id=accts["omnibus"].id,
                    amount=Decimal("500.00"),
                    type="FUNDING",
                    contract_id=accts["contract_id"],
                ),
                LedgerLeg(
                    debit_account_id=accts["omnibus"].id,
                    credit_account_id=accts["borrower"].id,
                    amount=Decimal("300.00"),
                    type="DISBURSEMENT",
                    contract_id=accts["contract_id"],
                ),
            ],
            idempotency_key=f"unbalanced-{uuid.uuid4().hex}",
        )
    await db_session.rollback()

    result = await db_session.execute(
        select(LedgerTransaction).where(LedgerTransaction.event_type == "BROKEN")
    )
    assert result.scalar_one_or_none() is None


async def test_post_transaction_multi_leg_repayment_split(db_session, funded_contract, make_user):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)
    fl_revenue = await get_or_create_account(
        db_session, account_type="FL_REVENUE", custodial_account_id=accts["custodial"].id
    )
    second_investor = await make_user(role="INVESTOR")
    other_lender = await get_or_create_account(
        db_session,
        account_type="LENDER",
        custodial_account_id=accts["custodial"].id,
        owner_user_id=uuid.UUID(second_investor["id"]),
        contract_id=accts["contract_id"],
    )

    txn = await post_transaction(
        db_session,
        event_type="REPAYMENT_SPLIT",
        legs=[
            LedgerLeg(
                debit_account_id=accts["borrower"].id,
                credit_account_id=accts["omnibus"].id,
                amount=Decimal("1000.00"),
                type="REPAYMENT",
                contract_id=accts["contract_id"],
            ),
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=accts["lender"].id,
                amount=Decimal("600.00"),
                type="DISTRIBUTION",
                contract_id=accts["contract_id"],
            ),
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=other_lender.id,
                amount=Decimal("300.00"),
                type="DISTRIBUTION",
                contract_id=accts["contract_id"],
            ),
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=fl_revenue.id,
                amount=Decimal("100.00"),
                type="FEE",
                contract_id=accts["contract_id"],
            ),
        ],
        idempotency_key=f"repayment-split-{uuid.uuid4().hex}",
    )
    await db_session.commit()

    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.ledger_transaction_id == txn.id))
    entries = result.scalars().all()
    assert len(entries) == 4
    assert sum(e.amount for e in entries if e.type == "DISTRIBUTION") == Decimal("900.00")
    assert await get_account_balance(db_session, accts["omnibus"].id) == Decimal("0.00")


async def test_post_transaction_idempotent_replay_returns_existing_and_writes_nothing(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)
    key = f"idem-{uuid.uuid4().hex}"
    legs = [
        LedgerLeg(
            debit_account_id=accts["omnibus"].id,
            credit_account_id=accts["borrower"].id,
            amount=Decimal("250.00"),
            type="DISBURSEMENT",
            contract_id=accts["contract_id"],
        )
    ]

    first = await post_transaction(db_session, event_type="DISBURSEMENT", legs=legs, idempotency_key=key)
    await db_session.commit()
    second = await post_transaction(db_session, event_type="DISBURSEMENT", legs=legs, idempotency_key=key)
    await db_session.commit()

    assert first.id == second.id
    result = await db_session.execute(
        select(LedgerTransaction).where(LedgerTransaction.idempotency_key == key)
    )
    assert len(result.scalars().all()) == 1
    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.ledger_transaction_id == first.id))
    assert len(result.scalars().all()) == 1


async def test_get_account_balance_is_sum_of_postings(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)

    await post_transaction(
        db_session,
        event_type="FUNDING",
        legs=[
            LedgerLeg(
                debit_account_id=accts["lender"].id,
                credit_account_id=accts["omnibus"].id,
                amount=Decimal("700.00"),
                type="FUNDING",
                contract_id=accts["contract_id"],
            )
        ],
        idempotency_key=f"balance-funding-{uuid.uuid4().hex}",
    )
    await post_transaction(
        db_session,
        event_type="DISBURSEMENT",
        legs=[
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=accts["borrower"].id,
                amount=Decimal("300.00"),
                type="DISBURSEMENT",
                contract_id=accts["contract_id"],
            )
        ],
        idempotency_key=f"balance-disb-{uuid.uuid4().hex}",
    )
    await db_session.commit()

    # OMNIBUS_CASH: +700 (credit from FUNDING) - 300 (debit from DISBURSEMENT) = 400
    assert await get_account_balance(db_session, accts["omnibus"].id) == Decimal("400.00")
    # Never reads a stored column -- there isn't one on LedgerAccount at all.
    assert not hasattr(LedgerAccount, "balance")


async def test_ledger_entries_update_blocked_by_db_trigger(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)
    txn = await post_transaction(
        db_session,
        event_type="DISBURSEMENT",
        legs=[
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=accts["borrower"].id,
                amount=Decimal("100.00"),
                type="DISBURSEMENT",
                contract_id=accts["contract_id"],
            )
        ],
        idempotency_key=f"trigger-update-{uuid.uuid4().hex}",
    )
    await db_session.commit()
    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.ledger_transaction_id == txn.id))
    entry = result.scalar_one()

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("UPDATE ledger_entries SET amount = :amount WHERE id = :id"),
            {"amount": Decimal("999.00"), "id": entry.id},
        )
    await db_session.rollback()


async def test_ledger_entries_delete_blocked_by_db_trigger(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)
    txn = await post_transaction(
        db_session,
        event_type="DISBURSEMENT",
        legs=[
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=accts["borrower"].id,
                amount=Decimal("100.00"),
                type="DISBURSEMENT",
                contract_id=accts["contract_id"],
            )
        ],
        idempotency_key=f"trigger-delete-{uuid.uuid4().hex}",
    )
    await db_session.commit()
    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.ledger_transaction_id == txn.id))
    entry = result.scalar_one()

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(text("DELETE FROM ledger_entries WHERE id = :id"), {"id": entry.id})
    await db_session.rollback()


async def test_ledger_transactions_update_blocked_by_db_trigger(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)
    txn = await post_transaction(
        db_session,
        event_type="DISBURSEMENT",
        legs=[
            LedgerLeg(
                debit_account_id=accts["omnibus"].id,
                credit_account_id=accts["borrower"].id,
                amount=Decimal("100.00"),
                type="DISBURSEMENT",
                contract_id=accts["contract_id"],
            )
        ],
        idempotency_key=f"trigger-header-update-{uuid.uuid4().hex}",
    )
    await db_session.commit()

    with pytest.raises(DBAPIError, match="append-only"):
        await db_session.execute(
            text("UPDATE ledger_transactions SET reference = :ref WHERE id = :id"),
            {"ref": "tampered", "id": txn.id},
        )
    await db_session.rollback()


async def test_only_one_platform_custodial_account_allowed(db_session):
    db_session.add(CustodialAccount(scope="PLATFORM"))
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


async def test_resolve_custodial_account_returns_platform_account_under_omnibus(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    contract_id = uuid.UUID(setup["contract"]["id"])

    account = await resolve_custodial_account(db_session, contract_id=contract_id)

    assert account.scope == "PLATFORM"
    assert account.contract_id is None
    # Any contract resolves to the same single platform account under omnibus.
    other_setup = await funded_contract(target_amount="5000.00", min_ticket="1000.00")
    other_account = await resolve_custodial_account(
        db_session, contract_id=uuid.UUID(other_setup["contract"]["id"])
    )
    assert other_account.id == account.id


async def test_ledger_type_check_accepts_funding(db_session, funded_contract):
    setup = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    accts = await _setup_accounts(db_session, setup)

    txn = await post_transaction(
        db_session,
        event_type="FUNDING",
        legs=[
            LedgerLeg(
                debit_account_id=accts["lender"].id,
                credit_account_id=accts["omnibus"].id,
                amount=Decimal("1234.56"),
                type="FUNDING",
                contract_id=accts["contract_id"],
            )
        ],
        idempotency_key=f"funding-type-{uuid.uuid4().hex}",
    )
    await db_session.commit()

    result = await db_session.execute(select(LedgerEntry).where(LedgerEntry.ledger_transaction_id == txn.id))
    entry = result.scalar_one()
    assert entry.type == "FUNDING"


async def test_cross_contract_transaction_rejected(db_session, funded_contract):
    setup_a = await funded_contract(target_amount="10000.00", min_ticket="1000.00")
    setup_b = await funded_contract(target_amount="5000.00", min_ticket="1000.00")
    accts_a = await _setup_accounts(db_session, setup_a)
    accts_b = await _setup_accounts(db_session, setup_b)

    with pytest.raises(CrossContractTransactionError):
        await post_transaction(
            db_session,
            event_type="CROSS_CONTRACT_ATTEMPT",
            legs=[
                LedgerLeg(
                    debit_account_id=accts_a["omnibus"].id,
                    credit_account_id=accts_a["borrower"].id,
                    amount=Decimal("100.00"),
                    type="DISBURSEMENT",
                    contract_id=accts_a["contract_id"],
                ),
                LedgerLeg(
                    debit_account_id=accts_b["omnibus"].id,
                    credit_account_id=accts_b["borrower"].id,
                    amount=Decimal("100.00"),
                    type="DISBURSEMENT",
                    contract_id=accts_b["contract_id"],
                ),
            ],
            idempotency_key=f"cross-contract-{uuid.uuid4().hex}",
        )
    await db_session.rollback()

    result = await db_session.execute(
        select(LedgerTransaction).where(LedgerTransaction.event_type == "CROSS_CONTRACT_ATTEMPT")
    )
    assert result.scalar_one_or_none() is None
