# Spec: Internal Ledger Foundation

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) — implemented via Sonnet |
| **Module** | `app/ledger/` (new module) |
| **Version** | 1.0 |
| **Date** | 2026-07-05 |
| **Related ADR** | ADR-002 (omnibus/custodial), ADR-003 (omnibus-first, escrow seam) |
| **Depends on** | Structural fixes (async DB layer) — merged |

---

## 1. Context & Goal

FundLok's `ledger_entries` table is the legal record of every fund movement, but today it is a **single-entry, contract-scoped movement log**: one row = `{type, amount, contract_id}` with no account references and no notion of *from → to*. It cannot express double-entry, cannot record lender **FUNDING** (that type isn't even in the CHECK constraint), and has no concept of the custodial account that ADR-003 requires for the escrow seam.

This spec defines the **foundation** the whole money system sits on: a double-entry, append-only ledger with an explicit chart of accounts mapped to `custodial_account`s, plus the DB-level immutability guarantee. It is deliberately upstream of and independent from the banking integration.

**Goal:** Evolve the ledger into an append-only, double-entry system with a `custodial_account`/`ledger_account` model (omnibus-first, escrow-ready per ADR-003), where every balance is computed by summation and no balance is ever stored mutably.

---

## 2. Out of Scope

- **Bank integration** — Brankas/direct-bank client, payment initiation, webhooks. (Separate banking spec.)
- **`bank_transactions` and reconciliation snapshots** — the link from a ledger event to an external bank settlement. This spec defines the internal ledger those will reconcile *against*; it does not define the external side. (Banking spec.)
- **Funding/disbursement/repayment/distribution endpoints and flows.** This spec provides the ledger primitives (post a balanced transaction, read a balance); the flows that call them are specced per feature.
- **Repayment schedule, share conversion, Decree 94 reporting.**
- **The `SELECT FOR UPDATE` disbursement lock** — belongs to the disbursement flow spec; noted here only because it locks a `contracts` row, not the ledger.
- **Migrating existing production ledger data** — Phase 0, assume no live ledger rows. If any exist in a shared DB, see Open Question #4.

---

## 3. Data Model

Double-entry model chosen: **balanced legs sharing a transaction group.** One economic event = one `ledger_transaction` (the idempotent header) with **two or more** `ledger_entries` (postings) that sum to zero across accounts. This keeps one-row-per-leg (close to today's table), moves idempotency to the event where it belongs, and supports multi-party events (a repayment that splits into DISTRIBUTION to N lenders + a FEE to FL is one transaction with many legs).

### New Table: `custodial_accounts`

Represents one physical bank account (ADR-003).

```
custodial_accounts
├── id                UUID          PK, default gen_random_uuid()
├── scope             TEXT          NOT NULL, CHECK IN ('PLATFORM','CONTRACT')
├── contract_id       UUID          nullable → references contracts(id) ON DELETE RESTRICT
│                                   -- NULL when scope='PLATFORM'; NOT NULL when scope='CONTRACT'
├── bank_account_ref  TEXT          nullable  -- external account identifier; NULL until a partner is signed
├── status            TEXT          NOT NULL, CHECK IN ('ACTIVE','CLOSED'), default 'ACTIVE'
├── created_at        TIMESTAMPTZ   DEFAULT NOW()
└── updated_at        TIMESTAMPTZ   DEFAULT NOW()
CONSTRAINTS:
  - CHECK ( (scope='PLATFORM' AND contract_id IS NULL) OR (scope='CONTRACT' AND contract_id IS NOT NULL) )
  - PARTIAL UNIQUE INDEX: at most one scope='PLATFORM' row  (uq_single_platform_custodial)
  - UNIQUE (contract_id) WHERE scope='CONTRACT'
```

At launch (omnibus): seed exactly one `PLATFORM` row. Under a future escrow migration: one `CONTRACT` row per contract.

### New Table: `ledger_accounts` (chart of accounts)

The internal accounts postings are made against. Every account belongs to exactly one `custodial_account`.

```
ledger_accounts
├── id                   UUID       PK, default gen_random_uuid()
├── account_type         TEXT       NOT NULL, CHECK IN
│                                   ('OMNIBUS_CASH','LENDER','BORROWER','FL_REVENUE','SUSPENSE')
├── custodial_account_id UUID       NOT NULL → references custodial_accounts(id) ON DELETE RESTRICT
├── owner_user_id        UUID       nullable → references users(id) ON DELETE RESTRICT
│                                   -- set for LENDER/BORROWER; NULL for OMNIBUS_CASH/FL_REVENUE/SUSPENSE
├── contract_id          UUID       nullable → references contracts(id) ON DELETE RESTRICT
│                                   -- set for contract-scoped positions; NULL for platform-level accounts
├── created_at           TIMESTAMPTZ DEFAULT NOW()
CONSTRAINTS:
  - UNIQUE (account_type, custodial_account_id, owner_user_id, contract_id)  -- one account per role/party/contract
```

Interpretation of balances: **Balance(account) = SUM(credits to account) − SUM(debits from account)** over all postings. Never stored.

### Modified Table: `ledger_entries` → becomes the postings table

Additive changes; existing columns preserved where they still make sense.

```
+ ledger_transaction_id  UUID   NOT NULL → references ledger_transactions(id) ON DELETE RESTRICT
+ debit_account_id       UUID   NOT NULL → references ledger_accounts(id) ON DELETE RESTRICT
+ credit_account_id      UUID   NOT NULL → references ledger_accounts(id) ON DELETE RESTRICT
- idempotency_key        moved to ledger_transactions (drop the column + its unique constraint here)
  (keep: id, contract_id, type, amount, reference, occurred_at, created_at, created_by)
  amount stays POSITIVE; direction is expressed by debit/credit account, not by sign.
CONSTRAINTS:
  - CHECK (amount > 0)
  - CHECK (debit_account_id <> credit_account_id)
  - update `type` CHECK to add 'FUNDING' and 'REFUND':
      type IN ('FUNDING','DISBURSEMENT','REPAYMENT','DISTRIBUTION','FEE','PENALTY','REFUND')
```

### New Table: `ledger_transactions` (the idempotent event header)

```
ledger_transactions
├── id                UUID          PK, default gen_random_uuid()
├── event_type        TEXT          NOT NULL  -- e.g. 'FUNDING','DISBURSEMENT','REPAYMENT_SPLIT'
├── contract_id       UUID          nullable → references contracts(id) ON DELETE RESTRICT
├── idempotency_key   TEXT          nullable, UNIQUE   -- the event-level idempotency anchor
├── reference         TEXT          nullable
├── occurred_at       TIMESTAMPTZ   NOT NULL, DEFAULT NOW()
├── created_by        UUID          nullable → references users(id) ON DELETE SET NULL
└── created_at        TIMESTAMPTZ   DEFAULT NOW()
```

**Balancing invariant (enforced in the posting service, verified by test):** for a given `ledger_transaction_id`, `SUM` over its legs of (credit side − debit side) per account nets to zero. The service writes all legs of a transaction inside one DB transaction, or none.

### Alembic Migration(s)

`alembic/versions/<hash>_ledger_double_entry_foundation.py` (revision id assigned at implementation; chains off current head — **do not** reuse the `0006` name from ADR-002/CLAUDE.md, that numbering is stale; use the hash chain). Creates `custodial_accounts`, `ledger_accounts`, `ledger_transactions`; alters `ledger_entries`; seeds one `PLATFORM` custodial account.

### DB-level immutability trigger

`ledger_transactions` and `ledger_entries` are append-only at the database layer. A PostgreSQL trigger (`BEFORE UPDATE OR DELETE`) raises an exception on both tables. Corrections are made by posting a new, reversing transaction — never by mutating a row. (ADR-002 called this "migration 0006"; implement it in this migration under the real hash chain.)

---

## 4. API Contract

This foundation exposes **internal service functions**, not public HTTP endpoints (the endpoints that call them live in feature specs). Define the service surface precisely so callers can build against it.

```python
# app/ledger/service.py  — all async, all AsyncSession

async def post_transaction(
    db: AsyncSession,
    *,
    event_type: str,
    legs: list[LedgerLeg],          # each: debit_account_id, credit_account_id, amount, type, contract_id
    idempotency_key: str | None,
    reference: str | None = None,
    created_by: UUID | None = None,
) -> LedgerTransaction:
    """Writes one balanced transaction + its legs atomically.
    - Rejects if legs do not balance (raises LedgerImbalanceError -> 422 at the caller).
    - If idempotency_key already exists, returns the existing transaction (no new rows)."""

async def get_account_balance(db: AsyncSession, account_id: UUID) -> Decimal:
    """SUM(credits) - SUM(debits) for the account. Never reads a stored balance."""

async def get_or_create_account(
    db: AsyncSession, *, account_type: str, custodial_account_id: UUID,
    owner_user_id: UUID | None = None, contract_id: UUID | None = None,
) -> LedgerAccount: ...

async def resolve_custodial_account(db: AsyncSession, *, contract_id: UUID) -> CustodialAccount:
    """OMNIBUS-FIRST SEAM: returns the single PLATFORM account today; under escrow returns the
    contract's CONTRACT account. Callers MUST route through this and never assume a global pool."""
```

There is no public financial write in this spec, so no `Idempotency-Key` header contract here — idempotency is enforced at `post_transaction` via `ledger_transactions.idempotency_key`.

---

## 5. State Machine

Not applicable — ledger rows have no lifecycle status; they are immutable facts. (`custodial_accounts.status` is `ACTIVE`/`CLOSED` but transitions are out of scope for this spec.)

---

## 6. Business Rules

1. **Double-entry:** every economic event is one `ledger_transaction` with ≥2 legs whose per-account net is zero. A caller cannot post an unbalanced transaction.
2. **Append-only:** no `UPDATE`/`DELETE` on `ledger_entries` or `ledger_transactions` at either the app layer or the DB layer (trigger). Reversals are new transactions.
3. **No stored balances:** any balance is `SUM` over postings at read time. No mutable balance column anywhere.
4. **Custodial indirection (ADR-003):** every `ledger_account` references a `custodial_account`. Callers resolve the custodial account via `resolve_custodial_account(contract_id)`, never by assuming a global pool.
5. **No cross-contract netting (ADR-003 invariant):** a single `ledger_transaction` must not move value between two different contracts' accounts. Contract funds are ring-fenced even under omnibus.
6. **Idempotency at event level:** replaying a `post_transaction` with an existing `idempotency_key` returns the original transaction and writes nothing. (This is the mechanism that will make bank webhooks safe in the banking spec.)
7. **Positive amounts:** `ledger_entries.amount > 0`; direction is carried by debit/credit account, never by sign.
8. **FL revenue** is a posting to an `FL_REVENUE` ledger account (a `FEE`-type leg), not a side effect — it is always visible in the ledger.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| `post_transaction` legs don't net to zero | Nothing written; raise `LedgerImbalanceError` | 422 at the calling endpoint |
| Replayed `idempotency_key` | Return existing transaction, write nothing | Existing transaction returned |
| Any `UPDATE`/`DELETE` attempted on `ledger_entries`/`ledger_transactions` (rogue query, ORM mistake) | DB trigger raises exception | Transaction aborts |
| `debit_account_id == credit_account_id` on a leg | CHECK constraint / service rejects | 422 |
| Attempt to create a second `PLATFORM` custodial account | Partial unique index violation | 409 / internal error |
| `resolve_custodial_account` for a contract with no account (escrow, not yet provisioned) | Raise `CustodialAccountNotProvisioned` | 409 at caller |

---

## 8. Acceptance Criteria

- [ ] `test_post_transaction_writes_balanced_legs_atomically` — a balanced 2-leg transaction persists a header + 2 postings.
- [ ] `test_post_transaction_rejects_unbalanced_legs` — legs that don't net to zero write nothing and raise.
- [ ] `test_post_transaction_multi_leg_repayment_split` — one REPAYMENT event with DISTRIBUTION legs to 2 lenders + a FEE leg to FL_REVENUE balances and persists.
- [ ] `test_post_transaction_idempotent_replay_returns_existing_and_writes_nothing` — same key twice = one transaction, one set of legs.
- [ ] `test_get_account_balance_is_sum_of_postings` — balance equals SUM(credits)−SUM(debits); no stored column read.
- [ ] `test_ledger_entries_update_blocked_by_db_trigger` — raw UPDATE raises at the DB layer.
- [ ] `test_ledger_entries_delete_blocked_by_db_trigger` — raw DELETE raises at the DB layer.
- [ ] `test_ledger_transactions_update_blocked_by_db_trigger` — same for the header table.
- [ ] `test_only_one_platform_custodial_account_allowed` — inserting a second PLATFORM row fails.
- [ ] `test_resolve_custodial_account_returns_platform_account_under_omnibus` — omnibus mode resolves the single PLATFORM account for any contract.
- [ ] `test_ledger_type_check_accepts_funding` — a FUNDING-type leg is accepted (regression on the enum gap).
- [ ] `test_cross_contract_transaction_rejected` — a transaction whose legs span two contracts' accounts is rejected (ADR-003 invariant).
- [ ] `test_migration_upgrade_and_downgrade_clean` — `alembic upgrade head` then `downgrade` runs clean; `alembic check` passes.

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Double-entry shape: `ledger_transactions` header + multi-leg `ledger_entries` vs a single-row two-account model. | Edward | **RESOLVED** — header + multi-leg (double-entry, as specified). |
| 2 | Should `SUSPENSE` accounts be in scope now, or deferred? | Edward | **RESOLVED** — provision the `SUSPENSE` account *type and shape* now (it is the structural home for confirmed-but-unattributed inbound funds in a webhook-driven system); build **no** suspense handling/sweep logic until the funding flow needs it. |
| 3 | Escrow provisioning trigger: what creates a contract's `CONTRACT` custodial account? | Edward | **RESOLVED** — fully automated, terminating in an **ADMIN approval gate** that can be short-circuited later once trusted. Dormant under omnibus. Requires a future ops-portal "Approve custodial account" control (frontend — Phat's spec). |
| 4 | Existing `ledger_entries` data requiring backfill? | Edward | **RESOLVED** — no data in the system; add the new account columns `NOT NULL` directly. |
| 5 | Does a lender ever need >1 LENDER account within one contract? | Edward | **RESOLVED** — no. Model is **one borrower to many lenders** per contract; the uniqueness key already supports N lenders via distinct `owner_user_id`. |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-07-05 | Edward | Initial draft — double-entry evolution, custodial/ledger account model, immutability trigger, escrow seam per ADR-003 |
| 0.2 | 2026-07-05 | Edward | Closed all 5 open questions; status → REVIEW. Confirmed header+multi-leg double-entry, SUSPENSE provisioned (no logic), escrow provisioning auto→ADMIN-gate, NOT NULL migration (no data), 1-borrower-to-many-lenders. |
| 1.0 | 2026-07-05 | Edward | Reviewed and ACCEPTED — cleared for implementation. |
