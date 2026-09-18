# Spec: Origination -- Schedule Generation

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/repayment_schedule/origination.py` |
| **Version** | 1.1 |
| **Date** | 2026-09-17 |
| **Related ADR** | — |
| **Depends on** | T6 (facility-data-model.md), T8 (business-day-calendar.md), T9 (facility-state-machine.md) |

---

## 1. Context & Goal

HANDOFF-03 T7: implement spec §4.1 exactly -- integer VND, floor division,
remainder absorbed entirely by the final instalment -- and reproduce the
§12.1 worked example to the đồng. This is the hard correctness bar the
handoff set: *"An implementation that does not reproduce these is wrong,
not approximately right."*

**Goal:** `compute_origination()` (pure arithmetic) and `originate_facility()`
(writes `facility` + `schedule_version` + N0 `scheduled_payment` rows) that
reproduce every number in §12.1 exactly, and fail loudly rather than write
a facility whose numbers do not reconcile.

---

## 2. Out of Scope

- Anything after origination: reconciliation (T10), the daily batch (T11),
  disbursement gating (T13).
- Re-amortization / extensions (§4.2, §4.4, §7 -- S4).
- The HTTP endpoint that would call `originate_facility()` from a contract
  -- not requested by T7's acceptance criteria; this spec is the
  computation and persistence, not the API surface.

---

## 3. Data Model

No new tables (writes into T6's `facility`, `schedule_version`,
`scheduled_payment`). No migration.

---

## 4. API Contract

Not an HTTP surface. The contract is the Python API:

```python
def compute_origination(
    *, principal_vnd: int, annual_rate_pct: Decimal,
    contractual_term_months: int, working_days_per_month: int = 22,
) -> OriginationResult: ...

def compute_backstop_day_index(business_day_count: int, working_days_per_month: int) -> int: ...

def originate_facility(
    db, *, contract_id: UUID, principal_vnd: int, annual_rate_pct: Decimal,
    contractual_term_months: int, payment_reference: str,
    start_date: date, calendar: BusinessDayCalendar,
    working_days_per_month: int = 22, actor_id: UUID | None = None,
) -> Facility: ...
```

`OriginationResult` carries `principal_vnd`, `interest_vnd`,
`total_obligation_vnd`, `business_day_count`, `daily_amount_vnd`,
`remainder_vnd`, `final_instalment_vnd`, `backstop_day_index`.

---

## 5. State Machine

`originate_facility()` creates the facility already in `DRAFT` and writes
one `state_transition` row (`from_status=None, to_status="DRAFT",
trigger="ORIGINATED"`) documenting creation -- not a transition through
`state_machine.py`'s `TRANSITIONS` table (which only covers moves *out of*
an existing state), but the same append-only audit trail.

---

## 6. Business Rules

1. `I = round(P * r/100 * x/12)` to the nearest whole đồng (round-half-up).
   The §12.1 example's own numbers divide evenly (no rounding is
   exercised by it), but integer VND requires *some* rule for inputs that
   do not.
2. `T0 = P + I`.
3. `N0 = x * working_days_per_month` (`working_days_per_month` defaults to
   22 per T5's params bump -- see `docs/specs/underwriting/grading-engine-deviations.md`
   if/when that spec is written).
4. `A0 = floor(T0 / N0)`; `remainder = T0 - A0*N0`; the **final** instalment
   only is `A0 + remainder` -- every other instalment is exactly `A0`.
5. `N_bs = min(ceil(4 * N0 / 3), 24 * D)` -- spec §4.5, confirmed against
   the committed source-of-truth spec (Open Question #1, below, is now
   closed). The `24 * D` cap is included but is dead logic while D15 caps
   the declared term at 12 months (`N0 <= 12*D` implies
   `ceil(4*N0/3) <= 16*D <= 24*D` always) -- see `origination.py`'s
   `BACKSTOP_ABSOLUTE_CAP_MONTHS` comment.
6. INV-5 (implied nominal rate <= 20%, §4.3/D12) and INV-13's contract-rate
   half (`r <= 20%`, Điều 468) are both enforced at origination:
   `compute_origination()` rejects `annual_rate_pct > 20` outright before
   computing anything, and `_assert_origination_invariants()` re-checks
   both as defense in depth.
7. The generated schedule always has exactly `N0` `scheduled_payment` rows,
   one per real business day (T8) starting from `start_date` -- a holiday
   or weekend consumes no slot and shifts nothing (T8 EC-01).
8. Every check in §7 below runs and raises **before** anything is added to
   the session -- an invariant failure halts that facility's origination
   entirely, per the handoff's instruction to fail loudly rather than
   continue with inconsistent state.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| `principal_vnd <= 0`, `contractual_term_months <= 0`, or `annual_rate_pct < 0` | `ValueError` before any computation | — |
| Reconstructed invariant check fails (see `_assert_origination_invariants`) | `OriginationInvariantError`, nothing added to the session | — |
| `start_date`'s year has no holiday-calendar entry (T8) | `MissingHolidayCalendarYearError` propagates from `calendar.generate_business_days` | — |

---

## 8. Acceptance Criteria

- [x] `test_worked_example_section_12_1_reproduces_to_the_dong` -- I, T0, N0, A0, remainder, final instalment, A0×87+final, **and N_bs=118**, all exact
- [x] `test_backstop_day_index_matches_section_4_5_table` -- 66→88, 132→176, 264→352
- [x] `test_backstop_day_index_absolute_cap_is_dead_logic_under_current_d15`
- [x] `test_implied_nominal_annual_rate_is_exactly_12_percent`
- [x] `test_remainder_is_always_absorbed_entirely_by_final_instalment` -- across several principal/rate/term combinations, not just the one worked example
- [x] `test_originate_facility_generates_full_schedule_and_sets_backstop` -- exactly N0 rows, first N0-1 all equal A0, last equals the final instalment, one ORIGINATED state_transition
- [x] `test_originate_facility_schedule_spans_tet_with_no_gap` -- T7/T8 integration
- [x] `test_compute_origination_rejects_non_positive_principal`, `test_compute_origination_rejects_non_positive_term`

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | ~~`N_bs`'s real formula (spec §4.5) could not be located anywhere in this repo.~~ | Edward | **Closed 2026-09-17.** The source-of-truth spec (`fixed-daily-repayment-mechanism-v1.3.md`) is now committed. §4.5 confirms `N_bs = min(ceil(4*N0/3), 24*D)`; its own table (66→88, 132→176, 264→352) rules out the `N0+30` alternative that was indistinguishable from the 4/3 ratio at the single original data point. `origination.py` and this spec are both updated. |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial origination/schedule-generation module (T7, HANDOFF-03). N_bs reconstructed pending source spec. |
| 1.1 | 2026-09-17 | Edward | Closed Open Question #1 against the committed source-of-truth spec: confirmed N_bs = min(ceil(4*N0/3), 24*D); added the 24*D cap (dead logic under current D15) and INV-5/INV-13 rate-cap enforcement at origination; corrected mislabeled invariant checks (what was called INV-5 is really INV-7, and vice versa). |
