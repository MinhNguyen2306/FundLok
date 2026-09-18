# Spec: Facility State Machine

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/repayment_schedule/state_machine.py` |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | — |
| **Depends on** | `docs/specs/repayment_schedule/facility-data-model.md` (T6) |

---

## 1. Context & Goal

HANDOFF-03 T9: the §5.3 transition table with its guards, states `DRAFT`
through `WRITTEN_OFF` (`UNDER_REVIEW` omitted per S4), every transition
writing a `state_transition` row with actor and trigger, and two named
invariants: INV-4 (no facility sits in `ACTIVE` or `ARREARS` past day
`N_bs` with a balance) and INV-9 (the transition into `WRITTEN_OFF` is
refused while `day_index <= N_bs`).

**Goal:** a single, table-driven state machine (`TRANSITIONS` in
`state_machine.py`) that T10/T11/T13 call to move a facility between
states, validated and guarded, with every move recorded append-only.

---

## 2. Out of Scope

- *When* to call a transition -- reconciliation (T10), the daily batch
  (T11) and funding (T13) own that decision; this spec is the mechanism
  they call into, not the scheduler.
- `grace_window` / `recovery_threshold` runtime config values (T11 --
  "pilot: 2 business days, 5 × A_current") -- guard functions here accept
  pre-computed booleans (`within_grace_window`, `grace_window_expired`) in
  their context rather than reading config themselves, so this module has
  no opinion on what those thresholds are.
- HTTP endpoints -- none are added by this spec.

---

## 3. Data Model

No new tables (uses `facility` / `state_transition` from T6). No migration.

---

## 4. API Contract

Not an HTTP surface. The contract is the Python API:

```python
apply_transition(
    db, facility, *,
    to_status: str, trigger: str,
    actor_id: UUID | None = None,
    context: dict | None = None,
    occurred_at: datetime | None = None,
) -> StateTransition
```

Raises `InvalidTransitionError` for a structurally unknown
`(from_status, to_status, trigger)`, or `TransitionGuardError` when the
move is known but its guard rejects it given `context`. Nothing is written
in either case.

`assert_inv4_no_stale_active_or_arrears(facility, *, day_index, balance_vnd)`
raises `TransitionGuardError` when INV-4 is violated; intended for T11's
daily batch and T20's invariant test suite to call once per facility per
run.

---

## 5. State Machine

```
DRAFT            ──[ADMIN_APPROVE]──────────────►  APPROVED
APPROVED         ──[DISBURSEMENT_POSTED]────────►  DISBURSED
DISBURSED        ──[SCHEDULE_ACTIVATED]─────────►  ACTIVE

ACTIVE           ──[CUTOFF_MISSED]──────────────►  ARREARS_WARNING
ARREARS_WARNING  ──[PAYMENT_WITHIN_GRACE_WINDOW]►  ACTIVE
ARREARS_WARNING  ──[GRACE_WINDOW_EXPIRED]───────►  ARREARS
ARREARS          ──[ARREARS_CLEARED]────────────►  ACTIVE
ARREARS          ──[RECOVERY_THRESHOLD_BREACHED]►  IN_RECOVERY

ACTIVE           ──[BACKSTOP_REACHED]───────────►  ACCELERATED
ARREARS          ──[BACKSTOP_REACHED]───────────►  ACCELERATED
ACCELERATED      ──[CURE_PERIOD_EXPIRED]────────►  IN_RECOVERY

ACTIVE           ──[OBLIGATION_SATISFIED]───────►  SETTLED
ACCELERATED      ──[OBLIGATION_SATISFIED]───────►  SETTLED
IN_RECOVERY      ──[OBLIGATION_SATISFIED]───────►  SETTLED

IN_RECOVERY      ──[MANUAL_WRITE_OFF]───────────►  WRITTEN_OFF
```

This is the exact §5.3 table (UNDER_REVIEW's two rows omitted per S4).
Three edges present in the original reconstruction are now removed
because §5.3 does not list them: `ARREARS_WARNING -> ACCELERATED`,
`ARREARS_WARNING -> SETTLED`, `ARREARS -> SETTLED`, and
`ACCELERATED -> WRITTEN_OFF`. A payoff received while in an arrears state
now clears the arrears first (`-> ACTIVE`) and settles from there
(`ACTIVE -> SETTLED`) -- two transitions instead of one, matching what
§5.3 actually authorizes rather than a shortcut. Write-off now routes
only through `IN_RECOVERY`, matching §4.5's "only if the cure period
expires unpaid does the facility move to IN_RECOVERY" -- going straight
from `ACCELERATED` skipped the cure period.

`SETTLED` and `WRITTEN_OFF` are terminal -- no outgoing transition is
valid from either.

**Transition rules:**

- `DRAFT -> APPROVED`, `APPROVED -> DISBURSED`, `DISBURSED -> ACTIVE`: no
  data guard at this layer (role/precondition checks belong to the calling
  service -- T13 for disbursement, an ops action for approval).
- `ARREARS_WARNING -> ACTIVE`: guarded on `context["within_grace_window"]`.
- `ARREARS_WARNING -> ARREARS`: guarded on `context["grace_window_expired"]`.
- `ARREARS -> ACTIVE`: guarded on `context["arrears_balance_vnd"] == 0`.
- `ARREARS -> IN_RECOVERY`: guarded on
  `context["arrears_balance_vnd"] >= context["recovery_threshold_vnd"]`.
  `recovery_threshold_vnd` is per-facility/product config the caller
  supplies -- §3/§8 do not define a concrete number, so this module takes
  it as given rather than hardcoding one.
- `{ACTIVE, ARREARS} -> ACCELERATED`: guarded on
  `context["day_index"] >= context["backstop_day_index"] and context["balance_vnd"] > 0`.
  Not `ARREARS_WARNING` -- §5.3 does not list that edge, and INV-4 does
  not require it either (INV-4 only covers `ACTIVE`/`ARREARS`).
- `ACCELERATED -> IN_RECOVERY`: guarded on
  `context["now"] > context["cure_period_ends"] and context["balance_vnd"] > 0`.
- `{ACTIVE, ACCELERATED, IN_RECOVERY} -> SETTLED`: guarded on
  `context["balance_vnd"] == 0`. Not `ARREARS_WARNING` or `ARREARS` --
  §5.3 has no direct arrears-to-settled row; those must clear the arrears
  first.
- `IN_RECOVERY -> WRITTEN_OFF`: guarded on INV-9 --
  `context["day_index"] > context["backstop_day_index"]`.

---

## 6. Business Rules

1. Every transition writes exactly one `state_transition` row (`facility_id`,
   `from_status`, `to_status`, `trigger`, `actor_id`, `metadata` = the guard
   context) -- the caller commits; `apply_transition` only adds to the
   session.
2. A transition either fully succeeds (facility status updated + row
   added) or raises before touching anything -- guards are checked before
   any mutation.
3. INV-9 is enforced as a hard guard on the `-> WRITTEN_OFF` edges. INV-4
   is not a transition guard (there is no transition to block a facility
   from "staying" ACTIVE) -- it is a liveness assertion the daily batch and
   T20's test suite call directly.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| `(from_status, to_status)` pair not in `TRANSITIONS` | `InvalidTransitionError` | — (Python exception; HTTP mapping is the calling router's job, none exists yet) |
| Valid pair, wrong `trigger` string | `InvalidTransitionError` | — |
| Valid pair + trigger, guard context fails the check | `TransitionGuardError` with the specific reason | — |
| Transition attempted from `SETTLED` or `WRITTEN_OFF` | `InvalidTransitionError` ("terminal state") | — |
| `WRITTEN_OFF` requested at `day_index <= backstop_day_index` | `TransitionGuardError` ("INV-9: ...") | — |

---

## 8. Acceptance Criteria

- [x] `test_happy_path_draft_to_active`
- [x] `test_rejects_unknown_from_to_pair`, `test_rejects_wrong_trigger_for_a_valid_pair`
- [x] `test_rejects_transition_out_of_terminal_state`, `test_written_off_terminal_state_also_rejects_further_transitions`
- [x] `test_settlement_requires_zero_balance`
- [x] `test_acceleration_requires_backstop_reached_with_positive_balance`
- [x] `test_acceleration_keeps_collecting_and_can_still_settle` -- INV-4/§6.3, acceleration is a demand not a suspension
- [x] `test_written_off_refused_while_day_index_at_or_before_backstop_inv9` -- INV-9 exactly
- [x] `test_arrears_escalation_and_grace_window_recovery`, `test_arrears_escalation_past_grace_window_then_cleared`
- [x] `test_arrears_escalates_to_recovery_on_threshold_breach` -- previously-missing ARREARS -> IN_RECOVERY edge
- [x] `test_settlement_from_arrears_states_requires_clearing_arrears_first` -- confirms the removed ARREARS(_WARNING) -> SETTLED shortcuts are gone
- [x] `test_arrears_warning_cannot_accelerate_directly` -- confirms the removed ARREARS_WARNING -> ACCELERATED edge is gone
- [x] `test_written_off_only_reachable_from_in_recovery_per_5_3` -- confirms the removed ACCELERATED -> WRITTEN_OFF edge is gone
- [x] `test_inv4_flags_stale_active_past_backstop_with_balance`, `test_inv4_does_not_fire_with_zero_balance_or_before_backstop`, `test_inv4_does_not_fire_for_accelerated_or_settled`

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | ~~The real §5.3 transition table (docx) was not found in this repo.~~ | Edward | **Closed 2026-09-17.** The source-of-truth spec is now committed. `TRANSITIONS` is reconciled against its §5.3 exactly (see §5 above for the three changes this made). |
| 2 | `originate_facility()` (T7) computes and persists `backstop_day_index` (and generates the full `scheduled_payment` set) at facility creation, while the facility is still `DRAFT`. §4.1 states origination sizing (`I, T0, N0, A0`) is "Executed once, on transition DISBURSED -> ACTIVE," and §8's `facility.backstop_date` note implies it derives from `disbursed_at`, which does not exist yet in `DRAFT`. This was not restructured as part of this correction pass -- it touches T6, T7 and T9 together, and splitting "sizing" (pure arithmetic, could run early, needed for the DRAFT -> APPROVED sizing-constraint guard per §4.1) from "schedule generation" (calendar-dependent, needs a start date) is a design call, not a bug fix. | Edward | **Open. Flagged, not fixed, in this correction pass.** |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial state machine (T9, HANDOFF-03). Reconstructed §5.3 pending source spec. |
| 1.1 | 2026-09-17 | Edward | Reconciled against the committed source-of-truth spec's real §5.3: added ARREARS -> IN_RECOVERY; removed ACCELERATED -> WRITTEN_OFF, ARREARS_WARNING -> SETTLED, ARREARS -> SETTLED, ARREARS_WARNING -> ACCELERATED. Closed Open Question #1; opened #2 on origination timing vs §4.1. |
