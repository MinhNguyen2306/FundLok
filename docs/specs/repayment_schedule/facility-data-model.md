# Spec: Facility Data Model

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/repayment_schedule/` |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | ADR-002 (ledger append-only pattern, reused here) |
| **Depends on** | `docs/specs/ledger/money-integer-vnd.md` (T1) |

---

## 1. Context & Goal

HANDOFF-03 T6: the fixed daily repayment mechanism (per "FundLok Fixed
Daily Repayment Mechanism Spec v1.3", Loc) needs a data model before
origination (T7), the business-day calendar (T8) or the state machine (T9)
can be built. Per the repayment-model decision record (12 Aug 2026): fixed
total obligation + fixed % of daily revenue, collected until satisfied,
duration = max(contractual term, actual time to satisfy).

**Goal:** five tables (`facility`, `schedule_version`, `scheduled_payment`,
`inbound_transfer`, `state_transition`) that can hold a fixed schedule from
origination through settlement, with the append-only and immutability
guarantees the spec's invariants (§10) require at the DB layer, not just in
application code.

---

## 2. Out of Scope (S4)

- `revenue_submission`, `extension`, `fee_ledger` tables -- extensions
  (§4.2, §4.4, §7) are out of MVP scope per S4.
- Any endpoint or service logic beyond the schema itself and the
  constraints/triggers that protect it. Origination logic is T7; the
  calendar is T8; the state machine transition logic is T9; reconciliation
  and the daily batch are T10/T11 -- none of those are this spec.
- `revenue-share`-driven repayment (VPBank's actual money model, per
  project memory) -- this spec builds the fixed-schedule mechanism
  HANDOFF-03 scoped for the 20 Sept demo, not the T-VAN-driven daily
  revenue share described for the live VPBank partnership.

---

## 3. Data Model

### New Table: `facility`

```
facility
├── id                        UUID          PK
├── contract_id               UUID          NOT NULL, UNIQUE → contracts(id) ON DELETE RESTRICT
├── principal_vnd              NUMERIC(20,0) NOT NULL, > 0                    -- P
├── annual_rate_pct            NUMERIC(6,3)  NOT NULL                          -- r
├── contractual_term_months    INTEGER       NOT NULL                          -- x
├── interest_vnd                NUMERIC(20,0) NOT NULL, >= 0                   -- I = P * r * x/12
├── total_obligation_vnd        NUMERIC(20,0) NOT NULL, > 0                    -- T0 = P + I
├── business_day_count          INTEGER       NOT NULL, > 0                    -- N0
├── backstop_day_index          INTEGER       nullable, >= business_day_count  -- N_bs, IMMUTABLE once set (INV-10)
├── backstop_date               DATE          nullable                        -- derived from backstop_day_index (T8)
├── status                     TEXT          NOT NULL, CHECK IN FACILITY_STATES, default 'DRAFT'
├── payment_reference           TEXT          NOT NULL, UNIQUE                 -- D20 matching key
├── disbursed_at                TIMESTAMPTZ   nullable
├── cure_period_ends            TIMESTAMPTZ   nullable                        -- set on ACCELERATED (T11)
├── collected_to_date_vnd        NUMERIC(20,0) NOT NULL, default 0             -- running projection, T10/T11
├── arrears_balance_vnd          NUMERIC(20,0) NOT NULL, default 0             -- running projection, T10/T11
├── created_at                 TIMESTAMPTZ   DEFAULT NOW()
└── updated_at                 TIMESTAMPTZ   DEFAULT NOW()
```

`FACILITY_STATES` (T9, §5.3, UNDER_REVIEW omitted per S4): `DRAFT`,
`APPROVED`, `DISBURSED`, `ACTIVE`, `ARREARS_WARNING`, `ARREARS`,
`ACCELERATED`, `IN_RECOVERY`, `SETTLED`, `WRITTEN_OFF`.

**DB-level guarantee (INV-10):** `backstop_day_index` may transition
`NULL -> value` exactly once; any further change is rejected by a BEFORE
UPDATE trigger (`facility_backstop_day_index_immutable_guard`). This is
column-level, not row-level -- `status`, `arrears_balance_vnd`, etc. stay
ordinarily mutable.

### New Table: `schedule_version`

```
schedule_version
├── id                     UUID          PK
├── facility_id             UUID          NOT NULL → facility(id) ON DELETE CASCADE
├── version_number          INTEGER       NOT NULL, default 1
├── daily_amount_vnd         NUMERIC(20,0) NOT NULL, > 0     -- A0 = floor(T0 / N0)
├── day_count               INTEGER       NOT NULL, > 0      -- N0
├── remainder_vnd            NUMERIC(20,0) NOT NULL, >= 0     -- T0 - A0*N0
├── final_instalment_vnd      NUMERIC(20,0) NOT NULL, > 0      -- A0 + remainder
└── created_at              TIMESTAMPTZ   DEFAULT NOW()

UNIQUE (facility_id, version_number)
```

Under S4 (no extensions, no re-amortization), exactly one row per facility
exists in practice; `version_number` is kept so a later extension spec has
somewhere to record a re-spread schedule without a schema change.

### New Table: `scheduled_payment`

```
scheduled_payment
├── id                      UUID          PK
├── facility_id              UUID          NOT NULL → facility(id) ON DELETE CASCADE
├── schedule_version_id       UUID          NOT NULL → schedule_version(id) ON DELETE CASCADE
├── day_index                INTEGER       NOT NULL, > 0     -- 1-based position
├── scheduled_date           DATE          NOT NULL          -- concrete business-day date (T8)
├── expected_amount_vnd       NUMERIC(20,0) NOT NULL, > 0
├── status                   TEXT          NOT NULL, CHECK IN ('PENDING','SATISFIED','MISSED'), default 'PENDING'
├── satisfied_amount_vnd      NUMERIC(20,0) NOT NULL, >= 0, default 0
├── satisfied_at              TIMESTAMPTZ   nullable
├── created_at               TIMESTAMPTZ   DEFAULT NOW()
└── updated_at               TIMESTAMPTZ   DEFAULT NOW()

UNIQUE (facility_id, scheduled_date)   -- INV-6
UNIQUE (facility_id, day_index)
```

### New Table: `inbound_transfer`

```
inbound_transfer
├── id                       UUID          PK
├── facility_id               UUID          nullable → facility(id) ON DELETE RESTRICT
├── source                   TEXT          NOT NULL              -- e.g. "CSV_IMPORT" (S2)
├── external_transaction_id   TEXT          NOT NULL, UNIQUE       -- bank's own natural key (INV-12/EC-18)
├── bank_reference            TEXT          NOT NULL              -- matched against facility.payment_reference (D20)
├── amount_vnd                NUMERIC(20,0) NOT NULL, > 0
├── value_date                DATE          NOT NULL
├── status                   TEXT          NOT NULL, CHECK IN ('UNMATCHED','MATCHED','APPLIED'), default 'UNMATCHED'
├── attributed_by             UUID          nullable → users(id) ON DELETE SET NULL
├── attributed_at             TIMESTAMPTZ   nullable
├── created_at                TIMESTAMPTZ   DEFAULT NOW()
└── updated_at                TIMESTAMPTZ   DEFAULT NOW()
```

`facility_id` is nullable: a transfer is matched to a facility by
`payment_reference` (D20) only after import (T10); an unmatched or
ambiguous transfer stays `UNMATCHED` (EC-11), never discarded, never
auto-applied on amount or payer-name guesswork.

### New Table: `state_transition` (append-only)

```
state_transition
├── id                UUID          PK
├── facility_id        UUID          NOT NULL → facility(id) ON DELETE CASCADE
├── from_status       TEXT          nullable, CHECK IN FACILITY_STATES  -- NULL only for the first transition
├── to_status         TEXT          NOT NULL, CHECK IN FACILITY_STATES
├── trigger           TEXT          NOT NULL     -- e.g. "ADMIN_APPROVE", "DISBURSEMENT_POSTED", "CUTOFF_BATCH"
├── actor_id           UUID          nullable → users(id) ON DELETE SET NULL  -- NULL for system/batch triggers
├── metadata          JSONB         nullable
├── occurred_at        TIMESTAMPTZ   NOT NULL, DEFAULT NOW()
└── created_at         TIMESTAMPTZ   DEFAULT NOW()
```

**DB-level guarantee:** append-only, via the same `ledger_immutability_guard()`
trigger function the ledger foundation migration (`862160bce972`) already
defines -- a BEFORE UPDATE/DELETE trigger raises on any attempt to mutate
or delete a row. Corrections are new rows, never edits.

### Alembic Migration

`alembic/versions/9142fb4c8540_facility_data_model.py`, chained off
`ca8a6db6183e` (T1's head).

---

## 4. API Contract

None. This spec is data-model-only; T7/T9 build services on top of it, and
no HTTP endpoint is introduced here.

---

## 5. State Machine

Table shape only -- see `docs/specs/repayment_schedule/facility-state-machine.md`
(T9) for the transition table and guards.

---

## 6. Business Rules

1. One `facility` per `contract` (`UNIQUE(contract_id)`) -- a contract
   moves onto a fixed schedule at most once under this data model.
2. `backstop_day_index >= business_day_count` always (CHECK constraint) --
   the backstop ceiling can never be shorter than the contractual schedule
   it bounds.
3. `total_obligation_vnd`, `daily_amount_vnd`, `business_day_count` are
   fixed at origination (T7) and never change afterward (S4 -- no
   re-amortization, no extensions in v1).
4. Bank statement reconciliation matches on `payment_reference` /
   `bank_reference` only (D20) -- never amount or payer name.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Second attempt to set `facility.backstop_day_index` after it is already set | BEFORE UPDATE trigger raises | DB exception (service layer maps to 500/409 -- not built in this spec) |
| Two scheduled payments on the same facility with the same `scheduled_date` | UNIQUE constraint violation | DB exception |
| Re-importing the same bank statement line (same `external_transaction_id`) | UNIQUE constraint violation -- caller/T10 catches and treats as "already imported" | — (T10, out of scope here) |
| Attempt to UPDATE or DELETE a `state_transition` row | BEFORE UPDATE/DELETE trigger raises | DB exception |

---

## 8. Acceptance Criteria

- [x] Migration chains off the current Alembic head with a hash revision ID
- [x] An attempt to UPDATE `facility.backstop_day_index` after it is set raises at the DB layer
- [x] A duplicate `inbound_transfer.external_transaction_id` import raises a unique violation
- [x] An UPDATE or DELETE on `state_transition` raises at the DB layer

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | ~~The backstop day-index formula (spec §4.5) is not in this repo.~~ | Edward | **Closed 2026-09-17.** The source-of-truth spec is now committed at `docs/specs/repayment_schedule/fixed-daily-repayment-mechanism-v1.3.md`. §4.5 confirms `N_bs = min(ceil(4*N0/3), 24*D)`, ruling out the `N0+30` alternative once considered indistinguishable at the single N0=88 data point. `app/repayment_schedule/origination.py` implements the confirmed formula including the `24*D` cap (dead logic today under D15's 12-month term limit, kept as a guard against a future D15 change). |
