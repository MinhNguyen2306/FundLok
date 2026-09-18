"""T9 (HANDOFF-03) -- facility state machine.

Pure mechanism tests: `apply_transition` only mutates the in-memory
`Facility` object and calls `db.add()` (a fake db stands in here), so these
run without a real database -- unlike most of this suite, which relies on
conftest.py's real-Postgres `db_session` fixture. `assert_inv4_no_stale_active_or_arrears`
is likewise pure.
"""
import uuid

import pytest

from app.repayment_schedule.models import Facility
from app.repayment_schedule.state_machine import (
    InvalidTransitionError,
    TransitionGuardError,
    apply_transition,
    assert_inv4_no_stale_active_or_arrears,
)


class _FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def _facility(status="DRAFT", backstop_day_index=None, business_day_count=88) -> Facility:
    return Facility(
        id=uuid.uuid4(),
        status=status,
        backstop_day_index=backstop_day_index,
        business_day_count=business_day_count,
    )


def test_happy_path_draft_to_active():
    facility = _facility()
    db = _FakeDB()

    apply_transition(db, facility, to_status="APPROVED", trigger="ADMIN_APPROVE")
    assert facility.status == "APPROVED"

    apply_transition(db, facility, to_status="DISBURSED", trigger="DISBURSEMENT_POSTED")
    assert facility.status == "DISBURSED"

    apply_transition(db, facility, to_status="ACTIVE", trigger="SCHEDULE_ACTIVATED")
    assert facility.status == "ACTIVE"

    transitions = [obj for obj in db.added if type(obj).__name__ == "StateTransition"]
    assert [t.trigger for t in transitions] == ["ADMIN_APPROVE", "DISBURSEMENT_POSTED", "SCHEDULE_ACTIVATED"]


def test_rejects_unknown_from_to_pair():
    facility = _facility(status="DRAFT")
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="Invalid state transition: DRAFT -> ACTIVE"):
        apply_transition(db, facility, to_status="ACTIVE", trigger="SCHEDULE_ACTIVATED")


def test_rejects_wrong_trigger_for_a_valid_pair():
    facility = _facility(status="ACTIVE")
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="trigger 'WRONG' is not valid"):
        apply_transition(db, facility, to_status="ARREARS_WARNING", trigger="WRONG")


def test_rejects_transition_out_of_terminal_state():
    facility = _facility(status="SETTLED")
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="terminal state"):
        apply_transition(db, facility, to_status="ACTIVE", trigger="SCHEDULE_ACTIVATED")


def test_written_off_terminal_state_also_rejects_further_transitions():
    facility = _facility(status="WRITTEN_OFF")
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="terminal state"):
        apply_transition(db, facility, to_status="SETTLED", trigger="OBLIGATION_SATISFIED")


def test_settlement_requires_zero_balance():
    facility = _facility(status="ACTIVE")
    db = _FakeDB()
    with pytest.raises(TransitionGuardError, match="obligation is not satisfied"):
        apply_transition(db, facility, to_status="SETTLED", trigger="OBLIGATION_SATISFIED", context={"balance_vnd": 1})

    apply_transition(db, facility, to_status="SETTLED", trigger="OBLIGATION_SATISFIED", context={"balance_vnd": 0})
    assert facility.status == "SETTLED"


def test_acceleration_requires_backstop_reached_with_positive_balance():
    facility = _facility(status="ACTIVE", backstop_day_index=118, business_day_count=88)
    db = _FakeDB()

    with pytest.raises(TransitionGuardError, match="backstop not reached"):
        apply_transition(
            db, facility, to_status="ACCELERATED", trigger="BACKSTOP_REACHED",
            context={"day_index": 100, "backstop_day_index": 118, "balance_vnd": 5000},
        )

    with pytest.raises(TransitionGuardError, match="backstop not reached"):
        apply_transition(
            db, facility, to_status="ACCELERATED", trigger="BACKSTOP_REACHED",
            context={"day_index": 120, "backstop_day_index": 118, "balance_vnd": 0},
        )

    apply_transition(
        db, facility, to_status="ACCELERATED", trigger="BACKSTOP_REACHED",
        context={"day_index": 120, "backstop_day_index": 118, "balance_vnd": 5000},
    )
    assert facility.status == "ACCELERATED"


def test_acceleration_keeps_collecting_and_can_still_settle():
    """T11 §6.3: "acceleration is a demand, not a suspension" -- an
    ACCELERATED facility can still reach SETTLED once its balance clears."""
    facility = _facility(status="ACCELERATED", backstop_day_index=118)
    db = _FakeDB()
    apply_transition(db, facility, to_status="SETTLED", trigger="OBLIGATION_SATISFIED", context={"balance_vnd": 0})
    assert facility.status == "SETTLED"


def test_written_off_only_reachable_from_in_recovery_per_5_3():
    """§5.3 lists only IN_RECOVERY -> WRITTEN_OFF -- write-off must route
    through the cure period (ACCELERATED -> IN_RECOVERY on cure expiry),
    never directly from ACCELERATED."""
    facility = _facility(status="ACCELERATED", backstop_day_index=118)
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="Invalid state transition: ACCELERATED -> WRITTEN_OFF"):
        apply_transition(
            db, facility, to_status="WRITTEN_OFF", trigger="MANUAL_WRITE_OFF",
            context={"day_index": 119, "backstop_day_index": 118},
        )


def test_written_off_refused_while_day_index_at_or_before_backstop_inv9():
    facility = _facility(status="IN_RECOVERY", backstop_day_index=118)
    db = _FakeDB()

    with pytest.raises(TransitionGuardError, match="INV-9"):
        apply_transition(
            db, facility, to_status="WRITTEN_OFF", trigger="MANUAL_WRITE_OFF",
            context={"day_index": 118, "backstop_day_index": 118},
        )

    apply_transition(
        db, facility, to_status="WRITTEN_OFF", trigger="MANUAL_WRITE_OFF",
        context={"day_index": 119, "backstop_day_index": 118},
    )
    assert facility.status == "WRITTEN_OFF"


def test_arrears_escalation_and_grace_window_recovery():
    facility = _facility(status="ACTIVE")
    db = _FakeDB()

    apply_transition(db, facility, to_status="ARREARS_WARNING", trigger="CUTOFF_MISSED")
    assert facility.status == "ARREARS_WARNING"

    with pytest.raises(TransitionGuardError, match="grace_window"):
        apply_transition(
            db, facility, to_status="ACTIVE", trigger="PAYMENT_WITHIN_GRACE_WINDOW",
            context={"within_grace_window": False},
        )

    apply_transition(
        db, facility, to_status="ACTIVE", trigger="PAYMENT_WITHIN_GRACE_WINDOW",
        context={"within_grace_window": True},
    )
    assert facility.status == "ACTIVE"


def test_arrears_escalation_past_grace_window_then_cleared():
    facility = _facility(status="ARREARS_WARNING")
    db = _FakeDB()

    apply_transition(
        db, facility, to_status="ARREARS", trigger="GRACE_WINDOW_EXPIRED",
        context={"grace_window_expired": True},
    )
    assert facility.status == "ARREARS"

    with pytest.raises(TransitionGuardError, match="arrears_balance_vnd"):
        apply_transition(
            db, facility, to_status="ACTIVE", trigger="ARREARS_CLEARED",
            context={"arrears_balance_vnd": 500},
        )

    apply_transition(db, facility, to_status="ACTIVE", trigger="ARREARS_CLEARED", context={"arrears_balance_vnd": 0})
    assert facility.status == "ACTIVE"


def test_arrears_escalates_to_recovery_on_threshold_breach():
    """§5.3 ARREARS -> IN_RECOVERY, 'threshold evaluation' /
    arrears_balance >= recovery_threshold -- previously missing entirely,
    so an ordinary (non-backstop) arrears facility had no escalation path
    at all."""
    facility = _facility(status="ARREARS")
    db = _FakeDB()

    with pytest.raises(TransitionGuardError, match="recovery_threshold_vnd"):
        apply_transition(
            db, facility, to_status="IN_RECOVERY", trigger="RECOVERY_THRESHOLD_BREACHED",
            context={"arrears_balance_vnd": 1_000_000, "recovery_threshold_vnd": 5_000_000},
        )

    apply_transition(
        db, facility, to_status="IN_RECOVERY", trigger="RECOVERY_THRESHOLD_BREACHED",
        context={"arrears_balance_vnd": 5_000_000, "recovery_threshold_vnd": 5_000_000},
    )
    assert facility.status == "IN_RECOVERY"


def test_settlement_from_arrears_states_requires_clearing_arrears_first():
    """§5.3 lists no ARREARS -> SETTLED or ARREARS_WARNING -> SETTLED row
    -- a payoff received while in arrears must clear the arrears
    (-> ACTIVE) before it can settle (ACTIVE -> SETTLED), not jump
    directly to SETTLED from an arrears state."""
    facility = _facility(status="ARREARS")
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="Invalid state transition: ARREARS -> SETTLED"):
        apply_transition(db, facility, to_status="SETTLED", trigger="OBLIGATION_SATISFIED", context={"balance_vnd": 0})

    facility_warning = _facility(status="ARREARS_WARNING")
    with pytest.raises(InvalidTransitionError, match="Invalid state transition: ARREARS_WARNING -> SETTLED"):
        apply_transition(
            db, facility_warning, to_status="SETTLED", trigger="OBLIGATION_SATISFIED", context={"balance_vnd": 0}
        )


def test_arrears_warning_cannot_accelerate_directly():
    """§5.3 lists no ARREARS_WARNING -> ACCELERATED row -- only ACTIVE and
    ARREARS may accelerate. Safe under INV-4, which does not cover
    ARREARS_WARNING."""
    facility = _facility(status="ARREARS_WARNING", backstop_day_index=118)
    db = _FakeDB()
    with pytest.raises(InvalidTransitionError, match="Invalid state transition: ARREARS_WARNING -> ACCELERATED"):
        apply_transition(
            db, facility, to_status="ACCELERATED", trigger="BACKSTOP_REACHED",
            context={"day_index": 120, "backstop_day_index": 118, "balance_vnd": 5000},
        )


def test_inv4_flags_stale_active_past_backstop_with_balance():
    facility = _facility(status="ACTIVE", backstop_day_index=118)
    with pytest.raises(TransitionGuardError, match="INV-4"):
        assert_inv4_no_stale_active_or_arrears(facility, day_index=119, balance_vnd=100)


def test_inv4_does_not_fire_with_zero_balance_or_before_backstop():
    facility = _facility(status="ACTIVE", backstop_day_index=118)
    assert_inv4_no_stale_active_or_arrears(facility, day_index=119, balance_vnd=0)
    assert_inv4_no_stale_active_or_arrears(facility, day_index=100, balance_vnd=100)


def test_inv4_does_not_fire_for_accelerated_or_settled():
    facility = _facility(status="ACCELERATED", backstop_day_index=118)
    assert_inv4_no_stale_active_or_arrears(facility, day_index=200, balance_vnd=100)
