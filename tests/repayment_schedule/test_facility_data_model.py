"""T6 (HANDOFF-03) -- facility data model DB-level guarantees.

No origination service exists yet (that's T7) -- these tests create
`Facility` rows directly via the ORM as setup, exactly the way
conftest.py's `approve_kyc_documents` fixture uses a direct ORM write for a
precondition with no service to call yet. The behavior under test here is
the migration's constraints and triggers, not an origination flow.
"""
import uuid
from datetime import date

import pytest
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.repayment_schedule.models import (
    Facility,
    InboundTransfer,
    ScheduledPayment,
    ScheduleVersion,
    StateTransition,
)


async def _make_facility(db_session, contract_id, *, business_day_count=88, backstop_day_index=None) -> Facility:
    facility = Facility(
        contract_id=contract_id,
        principal_vnd=300_000_000,
        annual_rate_pct="12.000",
        contractual_term_months=4,
        interest_vnd=12_000_000,
        total_obligation_vnd=312_000_000,
        business_day_count=business_day_count,
        backstop_day_index=backstop_day_index,
        payment_reference=f"FL-{uuid.uuid4().hex[:12]}",
    )
    db_session.add(facility)
    await db_session.commit()
    await db_session.refresh(facility)
    return facility


async def test_backstop_day_index_is_immutable_once_set(funded_contract, db_session):
    setup = await funded_contract(target_amount="10000000", min_ticket="1000000")
    facility = await _make_facility(db_session, setup["contract"]["id"], backstop_day_index=118)

    facility.backstop_day_index = 200
    db_session.add(facility)
    with pytest.raises((DBAPIError, IntegrityError)):
        await db_session.commit()
    await db_session.rollback()


async def test_backstop_day_index_can_be_set_once_from_null(funded_contract, db_session):
    setup = await funded_contract(target_amount="10000000", min_ticket="1000000")
    facility = await _make_facility(db_session, setup["contract"]["id"], backstop_day_index=None)

    facility.backstop_day_index = 118
    db_session.add(facility)
    await db_session.commit()  # NULL -> value is allowed exactly once
    await db_session.refresh(facility)
    assert facility.backstop_day_index == 118


async def test_backstop_day_index_cannot_be_less_than_business_day_count(funded_contract, db_session):
    setup = await funded_contract(target_amount="10000000", min_ticket="1000000")
    with pytest.raises(IntegrityError):
        await _make_facility(
            db_session, setup["contract"]["id"], business_day_count=88, backstop_day_index=50
        )
    await db_session.rollback()


async def test_scheduled_payment_rejects_duplicate_date_on_same_facility(funded_contract, db_session):
    setup = await funded_contract(target_amount="10000000", min_ticket="1000000")
    facility = await _make_facility(db_session, setup["contract"]["id"])
    version = ScheduleVersion(
        facility_id=facility.id,
        daily_amount_vnd=3_545_454,
        day_count=88,
        remainder_vnd=48,
        final_instalment_vnd=3_545_502,
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    same_date = date(2026, 10, 1)
    db_session.add(
        ScheduledPayment(
            facility_id=facility.id,
            schedule_version_id=version.id,
            day_index=1,
            scheduled_date=same_date,
            expected_amount_vnd=3_545_454,
        )
    )
    await db_session.commit()

    db_session.add(
        ScheduledPayment(
            facility_id=facility.id,
            schedule_version_id=version.id,
            day_index=2,
            scheduled_date=same_date,  # INV-6 violation: same facility, same date
            expected_amount_vnd=3_545_454,
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_inbound_transfer_rejects_duplicate_external_transaction_id(db_session):
    external_id = f"BANK-TXN-{uuid.uuid4().hex[:10]}"
    db_session.add(
        InboundTransfer(
            source="CSV_IMPORT",
            external_transaction_id=external_id,
            bank_reference="FL-0001",
            amount_vnd=1_000_000,
            value_date=date(2026, 10, 1),
        )
    )
    await db_session.commit()

    db_session.add(
        InboundTransfer(
            source="CSV_IMPORT",
            external_transaction_id=external_id,  # re-import of the same statement line
            bank_reference="FL-0001",
            amount_vnd=1_000_000,
            value_date=date(2026, 10, 1),
        )
    )
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_state_transition_is_append_only(funded_contract, db_session):
    setup = await funded_contract(target_amount="10000000", min_ticket="1000000")
    facility = await _make_facility(db_session, setup["contract"]["id"])

    transition = StateTransition(
        facility_id=facility.id,
        from_status=None,
        to_status="DRAFT",
        trigger="ORIGINATION",
    )
    db_session.add(transition)
    await db_session.commit()
    await db_session.refresh(transition)

    transition.to_status = "APPROVED"
    db_session.add(transition)
    with pytest.raises((DBAPIError, IntegrityError)):
        await db_session.commit()
    await db_session.rollback()
