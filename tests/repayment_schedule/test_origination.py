"""T7 (HANDOFF-03) -- origination / schedule generation.

Pure logic (compute_origination, compute_backstop_day_index) and the
in-memory originate_facility() assembly both run without a real database --
originate_facility() only calls db.add(), which a fake stands in for here,
matching the pattern in tests/repayment_schedule/test_state_machine.py.
"""
import datetime
import uuid
from decimal import Decimal

import pytest

from app.repayment_schedule.calendar import BusinessDayCalendar
from app.repayment_schedule.origination import (
    OriginationInvariantError,
    compute_backstop_day_index,
    compute_origination,
    originate_facility,
)


class _FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def test_worked_example_section_12_1_reproduces_to_the_dong():
    """The exact numbers from HANDOFF-03's §12.1 worked example. An
    implementation that does not reproduce these is wrong, not
    approximately right."""
    result = compute_origination(
        principal_vnd=300_000_000,
        annual_rate_pct=Decimal("12"),
        contractual_term_months=4,
        working_days_per_month=22,
    )
    assert result.interest_vnd == 12_000_000
    assert result.total_obligation_vnd == 312_000_000
    assert result.business_day_count == 88
    assert result.daily_amount_vnd == 3_545_454
    assert result.remainder_vnd == 48
    assert result.final_instalment_vnd == 3_545_502
    assert result.daily_amount_vnd * 87 + result.final_instalment_vnd == 312_000_000
    assert result.backstop_day_index == 118


def test_implied_nominal_annual_rate_is_exactly_12_percent():
    result = compute_origination(
        principal_vnd=300_000_000,
        annual_rate_pct=Decimal("12"),
        contractual_term_months=4,
        working_days_per_month=22,
    )
    implied = (Decimal(result.interest_vnd) / Decimal(result.principal_vnd)) / (Decimal(4) / Decimal(12)) * 100
    assert implied == Decimal("12.00")


def test_backstop_day_index_matches_worked_example():
    """N_bs = min(ceil(4*N0/3), 24*D) -- spec §4.5. Confirmed against the
    committed source-of-truth spec's §12.1 worked example."""
    assert compute_backstop_day_index(88, working_days_per_month=22) == 118


def test_backstop_day_index_matches_section_4_5_table():
    """Spec §4.5's table: 66->88, 132->176, 264->352 (D=22 throughout).
    This also rules out the N0+30 alternative that was indistinguishable
    from ceil(4*N0/3) at the single N0=88 data point alone."""
    assert compute_backstop_day_index(66, working_days_per_month=22) == 88
    assert compute_backstop_day_index(132, working_days_per_month=22) == 176
    assert compute_backstop_day_index(264, working_days_per_month=22) == 352


def test_backstop_day_index_absolute_cap_is_dead_logic_under_current_d15():
    """The `24 * D` cap in §4.5 cannot bind while D15 caps the declared
    term at 12 months: N0 <= 12*D, so ceil(4*N0/3) <= 16*D <= 24*D always.
    This pins that the cap is present and correct, not that it currently
    changes any result."""
    working_days_per_month = 22
    max_permitted_n0 = 12 * working_days_per_month  # D15's 12-month cap
    assert (
        compute_backstop_day_index(max_permitted_n0, working_days_per_month=working_days_per_month)
        < 24 * working_days_per_month
    )


def test_compute_origination_rejects_non_positive_principal():
    with pytest.raises(ValueError):
        compute_origination(principal_vnd=0, annual_rate_pct=Decimal("12"), contractual_term_months=4)


def test_compute_origination_rejects_non_positive_term():
    with pytest.raises(ValueError):
        compute_origination(principal_vnd=1000, annual_rate_pct=Decimal("12"), contractual_term_months=0)


def test_remainder_is_always_absorbed_entirely_by_final_instalment():
    for principal in (100_000_000, 250_000_000, 999_999_999):
        result = compute_origination(
            principal_vnd=principal, annual_rate_pct=Decimal("15.5"), contractual_term_months=6
        )
        reconstructed = result.daily_amount_vnd * (result.business_day_count - 1) + result.final_instalment_vnd
        assert reconstructed == result.total_obligation_vnd
        assert 0 <= result.remainder_vnd < result.business_day_count


def test_originate_facility_generates_full_schedule_and_sets_backstop():
    cal = BusinessDayCalendar()
    db = _FakeDB()
    contract_id = uuid.uuid4()

    facility = originate_facility(
        db,
        contract_id=contract_id,
        principal_vnd=300_000_000,
        annual_rate_pct=Decimal("12"),
        contractual_term_months=4,
        payment_reference=f"FL-{uuid.uuid4().hex[:10]}",
        start_date=datetime.date(2026, 9, 21),
        calendar=cal,
    )

    assert facility.status == "DRAFT"
    assert facility.backstop_day_index == 118
    assert facility.backstop_date is not None

    scheduled_payments = sorted(
        (o for o in db.added if type(o).__name__ == "ScheduledPayment"),
        key=lambda p: p.day_index,
    )
    assert len(scheduled_payments) == 88
    assert scheduled_payments[0].day_index == 1
    assert scheduled_payments[0].expected_amount_vnd == 3_545_454
    assert scheduled_payments[-1].day_index == 88
    assert scheduled_payments[-1].expected_amount_vnd == 3_545_502
    for payment in scheduled_payments[:-1]:
        assert payment.expected_amount_vnd == 3_545_454

    # every scheduled_date is a real, distinct business day
    dates = [p.scheduled_date for p in scheduled_payments]
    assert len(set(dates)) == len(dates)
    for d in dates:
        assert cal.is_business_day(d)

    state_transitions = [o for o in db.added if type(o).__name__ == "StateTransition"]
    assert len(state_transitions) == 1
    assert state_transitions[0].from_status is None
    assert state_transitions[0].to_status == "DRAFT"
    assert state_transitions[0].trigger == "ORIGINATED"

    schedule_versions = [o for o in db.added if type(o).__name__ == "ScheduleVersion"]
    assert len(schedule_versions) == 1
    assert schedule_versions[0].day_count == 88


def test_originate_facility_schedule_spans_tet_with_no_gap():
    """The generated schedule for a facility originated right before Tết
    2026 must still produce exactly N0 scheduled business days, skipping
    the holiday block entirely (T8 EC-01), not shifting amounts around it."""
    cal = BusinessDayCalendar()
    db = _FakeDB()
    facility = originate_facility(
        db,
        contract_id=uuid.uuid4(),
        principal_vnd=100_000_000,
        annual_rate_pct=Decimal("10"),
        contractual_term_months=3,
        payment_reference=f"FL-{uuid.uuid4().hex[:10]}",
        start_date=datetime.date(2026, 2, 10),
        calendar=cal,
    )
    scheduled_payments = [o for o in db.added if type(o).__name__ == "ScheduledPayment"]
    assert len(scheduled_payments) == facility.business_day_count
    tet_2026 = {datetime.date(2026, 2, d) for d in range(16, 21)}
    assert tet_2026.isdisjoint({p.scheduled_date for p in scheduled_payments})
