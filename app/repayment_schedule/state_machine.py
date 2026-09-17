"""Facility state machine (T9), reconciled against the committed
source-of-truth spec's §5.3 transition table
(`docs/specs/repayment_schedule/fixed-daily-repayment-mechanism-v1.3.md`).

UNDER_REVIEW and its two transitions (ACTIVE <-> UNDER_REVIEW) are
intentionally omitted: S4 ("Extensions are out of MVP scope") explicitly
excludes §4.2/§4.4/§7 and instructs "omit UNDER_REVIEW (S4)" -- this is a
settled scope decision, not a gap, and matches T10/T14/T16 remaining
blocked.

This table was originally reconstructed (the source docx was not yet
committed) and has since been corrected against the real §5.3 in three
ways:
  1. Added ARREARS -> IN_RECOVERY (threshold evaluation) -- without it,
     ordinary arrears could never escalate to recovery, only to
     acceleration by reaching the backstop.
  2. Removed ACCELERATED -> WRITTEN_OFF -- §5.3 routes write-off only
     through IN_RECOVERY -> WRITTEN_OFF; going straight from ACCELERATED
     skips the cure period, contradicting §4.5's "only if the cure period
     expires unpaid does the facility move to IN_RECOVERY."
  3. Removed ARREARS_WARNING -> SETTLED, ARREARS -> SETTLED, and
     ARREARS_WARNING -> ACCELERATED -- none of these three appear as rows
     in §5.3. A full payoff received while in arrears now clears the
     arrears first (-> ACTIVE, guard arrears_balance=0) and settles from
     there (ACTIVE -> SETTLED, guard B=0), which is two transitions, not
     one, but each is one §5.3 requires. Dropping ARREARS_WARNING ->
     ACCELERATED is safe under INV-4, which only requires no facility
     remain in ACTIVE or ARREARS (not ARREARS_WARNING) past N_bs with a
     balance -- ARREARS_WARNING's grace window is short enough that the
     daily batch resolves it to ACTIVE or ARREARS before the next
     backstop evaluation runs.

This module is pure mechanism: `apply_transition()` validates a requested
move against the table, runs its guard (if any) against a caller-supplied
context, writes the facility's new status and one append-only
`state_transition` row, and returns it. It does not decide *when* to call
itself -- that is T10 (reconciliation), T11 (daily batch) and T13
(funding), none of which are in this handoff's scope.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional
from uuid import UUID

from app.repayment_schedule.models import FACILITY_STATES, Facility, StateTransition


class InvalidTransitionError(Exception):
    """Raised when (from_status, to_status, trigger) is not in TRANSITIONS,
    or from_status is a terminal state (SETTLED, WRITTEN_OFF)."""


class TransitionGuardError(Exception):
    """Raised when the transition is structurally valid but its guard
    rejects it given the supplied context (e.g. WRITTEN_OFF requested
    before day_index > backstop_day_index -- INV-9)."""


TERMINAL_STATES = frozenset({"SETTLED", "WRITTEN_OFF"})


def _backstop_reached_guard(ctx: dict) -> tuple[bool, str]:
    day_index = ctx["day_index"]
    backstop_day_index = ctx["backstop_day_index"]
    balance = ctx["balance_vnd"]
    if backstop_day_index is None:
        return False, "backstop_day_index has not been set for this facility"
    if not (day_index >= backstop_day_index and balance > 0):
        return False, (
            f"backstop not reached: day_index={day_index}, "
            f"backstop_day_index={backstop_day_index}, balance_vnd={balance}"
        )
    return True, ""


def _within_grace_window_guard(ctx: dict) -> tuple[bool, str]:
    if not ctx.get("within_grace_window"):
        return False, "payment was not received within the configured grace_window"
    return True, ""


def _grace_window_expired_guard(ctx: dict) -> tuple[bool, str]:
    if not ctx.get("grace_window_expired"):
        return False, "grace_window has not yet expired"
    return True, ""


def _arrears_cleared_guard(ctx: dict) -> tuple[bool, str]:
    if ctx["arrears_balance_vnd"] != 0:
        return False, f"arrears_balance_vnd is {ctx['arrears_balance_vnd']}, not 0"
    return True, ""


def _recovery_threshold_breached_guard(ctx: dict) -> tuple[bool, str]:
    """§5.3 ARREARS -> IN_RECOVERY: 'Threshold evaluation' / arrears_balance
    >= recovery_threshold. recovery_threshold is per-facility/product
    config, supplied by the caller in context -- it is not itself defined
    anywhere in §3/§8, so this guard takes it as given rather than
    hardcoding a number the spec does not state."""
    arrears_balance = ctx["arrears_balance_vnd"]
    recovery_threshold = ctx["recovery_threshold_vnd"]
    if not (arrears_balance >= recovery_threshold):
        return False, (
            f"arrears_balance_vnd ({arrears_balance}) has not reached "
            f"recovery_threshold_vnd ({recovery_threshold})"
        )
    return True, ""


def _balance_zero_guard(ctx: dict) -> tuple[bool, str]:
    if ctx["balance_vnd"] != 0:
        return False, f"balance_vnd is {ctx['balance_vnd']}, obligation is not satisfied"
    return True, ""


def _cure_period_expired_guard(ctx: dict) -> tuple[bool, str]:
    now = ctx["now"]
    cure_period_ends = ctx["cure_period_ends"]
    balance = ctx["balance_vnd"]
    if cure_period_ends is None:
        return False, "cure_period_ends is not set"
    if not (now > cure_period_ends and balance > 0):
        return False, f"cure period has not expired (now={now}, cure_period_ends={cure_period_ends}) or balance is 0"
    return True, ""


def _written_off_guard(ctx: dict) -> tuple[bool, str]:
    """INV-9: the transition into WRITTEN_OFF is refused while
    day_index <= backstop_day_index (N_bs)."""
    day_index = ctx["day_index"]
    backstop_day_index = ctx["backstop_day_index"]
    if backstop_day_index is None or not (day_index > backstop_day_index):
        return False, (
            f"INV-9: cannot write off while day_index ({day_index}) <= "
            f"backstop_day_index ({backstop_day_index})"
        )
    return True, ""


@dataclass(frozen=True)
class TransitionRule:
    triggers: frozenset[str]
    guard: Optional[Callable[[dict], tuple[bool, str]]] = None


# (from_status, to_status) -> allowed triggers + optional guard.
# Guard context keys, supplied by the caller per transition:
#   day_index, backstop_day_index, balance_vnd, arrears_balance_vnd,
#   recovery_threshold_vnd, within_grace_window, grace_window_expired,
#   now, cure_period_ends
TRANSITIONS: dict[tuple[str, str], TransitionRule] = {
    ("DRAFT", "APPROVED"): TransitionRule(frozenset({"ADMIN_APPROVE"})),
    ("APPROVED", "DISBURSED"): TransitionRule(frozenset({"DISBURSEMENT_POSTED"})),
    ("DISBURSED", "ACTIVE"): TransitionRule(frozenset({"SCHEDULE_ACTIVATED"})),
    ("ACTIVE", "ARREARS_WARNING"): TransitionRule(frozenset({"CUTOFF_MISSED"})),
    ("ARREARS_WARNING", "ACTIVE"): TransitionRule(
        frozenset({"PAYMENT_WITHIN_GRACE_WINDOW"}), guard=_within_grace_window_guard
    ),
    ("ARREARS_WARNING", "ARREARS"): TransitionRule(
        frozenset({"GRACE_WINDOW_EXPIRED"}), guard=_grace_window_expired_guard
    ),
    ("ARREARS", "ACTIVE"): TransitionRule(frozenset({"ARREARS_CLEARED"}), guard=_arrears_cleared_guard),
    ("ARREARS", "IN_RECOVERY"): TransitionRule(
        frozenset({"RECOVERY_THRESHOLD_BREACHED"}), guard=_recovery_threshold_breached_guard
    ),
    ("ACTIVE", "ACCELERATED"): TransitionRule(frozenset({"BACKSTOP_REACHED"}), guard=_backstop_reached_guard),
    ("ARREARS", "ACCELERATED"): TransitionRule(frozenset({"BACKSTOP_REACHED"}), guard=_backstop_reached_guard),
    ("ACCELERATED", "IN_RECOVERY"): TransitionRule(
        frozenset({"CURE_PERIOD_EXPIRED"}), guard=_cure_period_expired_guard
    ),
    ("ACTIVE", "SETTLED"): TransitionRule(frozenset({"OBLIGATION_SATISFIED"}), guard=_balance_zero_guard),
    ("ACCELERATED", "SETTLED"): TransitionRule(frozenset({"OBLIGATION_SATISFIED"}), guard=_balance_zero_guard),
    ("IN_RECOVERY", "SETTLED"): TransitionRule(frozenset({"OBLIGATION_SATISFIED"}), guard=_balance_zero_guard),
    ("IN_RECOVERY", "WRITTEN_OFF"): TransitionRule(frozenset({"MANUAL_WRITE_OFF"}), guard=_written_off_guard),
}


def validate_transition(from_status: str, to_status: str, trigger: str) -> None:
    if from_status in TERMINAL_STATES:
        raise InvalidTransitionError(f"{from_status} is a terminal state; no transition out of it is valid")
    if to_status not in FACILITY_STATES:
        raise InvalidTransitionError(f"{to_status!r} is not a known facility state")
    rule = TRANSITIONS.get((from_status, to_status))
    if rule is None:
        raise InvalidTransitionError(f"Invalid state transition: {from_status} -> {to_status}")
    if trigger not in rule.triggers:
        raise InvalidTransitionError(
            f"trigger {trigger!r} is not valid for {from_status} -> {to_status} "
            f"(expected one of {sorted(rule.triggers)})"
        )


def apply_transition(
    db,
    facility: Facility,
    *,
    to_status: str,
    trigger: str,
    actor_id: Optional[UUID] = None,
    context: Optional[dict] = None,
    occurred_at: Optional[datetime] = None,
) -> StateTransition:
    """Validate and apply one facility state transition, writing an
    append-only `state_transition` row. Raises InvalidTransitionError for a
    structurally unknown move, or TransitionGuardError when the move is
    known but its guard rejects it given `context`. Nothing is written on
    either error."""
    from_status = facility.status
    validate_transition(from_status, to_status, trigger)

    rule = TRANSITIONS[(from_status, to_status)]
    if rule.guard is not None:
        ok, reason = rule.guard(context or {})
        if not ok:
            raise TransitionGuardError(f"{from_status} -> {to_status} rejected: {reason}")

    facility.status = to_status
    db.add(facility)

    transition = StateTransition(
        facility_id=facility.id,
        from_status=from_status,
        to_status=to_status,
        trigger=trigger,
        actor_id=actor_id,
        metadata_=context if context else None,
        **({"occurred_at": occurred_at} if occurred_at is not None else {}),
    )
    db.add(transition)
    return transition


def assert_inv4_no_stale_active_or_arrears(facility: Facility, *, day_index: int, balance_vnd) -> None:
    """INV-4: no facility sits in ACTIVE or ARREARS past day N_bs with a
    balance. This is a liveness invariant on the daily batch (T11), not a
    transition guard -- there is no transition to block; the assertion
    exists for T11/T20 to call once per facility per batch run, and fails
    loudly (per the handoff's instruction that every invariant "fails
    loudly and halts the affected facility's processing") rather than
    continuing with inconsistent state.
    """
    if (
        facility.status in ("ACTIVE", "ARREARS")
        and facility.backstop_day_index is not None
        and day_index > facility.backstop_day_index
        and balance_vnd > 0
    ):
        raise TransitionGuardError(
            f"INV-4 violated: facility {facility.id} is {facility.status} at day_index={day_index}, "
            f"past backstop_day_index={facility.backstop_day_index}, with balance_vnd={balance_vnd}"
        )
