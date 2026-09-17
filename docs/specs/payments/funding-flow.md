# Spec: Funding Flow — Ledger Legs for Money Movement

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/payments/` (rewrite), `app/ledger/` (migration only) |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | ADR-002 (omnibus/custodial), ADR-003 (omnibus-first, escrow seam) |
| **Depends on** | `docs/specs/ledger/ledger-foundation.md` (ACCEPTED v1.0), HANDOFF-03 §5.2 (T0f) |
| **Blocks** | T10 (funding/disbursement/repayment endpoints), T14 (repayment split + FEE leg) |

---

## 1. Context & Goal

`docs/specs/ledger/ledger-foundation.md` gave FundLok a double-entry ledger primitive (`post_transaction`, balanced legs, a five-type chart of accounts) but deliberately left "the flows that call it" — funding, disbursement, repayment, distribution — to be specced per feature (foundation spec §2, "Out of Scope"). `app/payments/service.py` today is a **compatibility shim**, not that spec: it keeps the old single-leg `DISBURSEMENT`/`REPAYMENT`/`DISTRIBUTION` shapes alive against the new schema, and no `FUNDING` leg has ever been posted at all (HANDOFF-03 Issue 11).

Two decisions were forced the moment `FUNDING` became real (HANDOFF-03 §5.2, "T0f"), because they fix the meaning of every investor- and borrower-facing balance the platform will ever display, and unwinding them later means restating history:

- **Issue 15 — what does a `LENDER` balance mean?** Resolved: the investor's **outstanding claim** on that contract, not cumulative cash returned. `LENDER` is **credited** when the claim is established (at `FUNDING`) and **debited** by `DISTRIBUTION` as the claim is paid down.
- **Issue 16 — where does uncommitted investor cash live?** Resolved: a new platform-level account type, `INVESTOR_CASH`, distinct from `SUSPENSE` (which stays reserved for confirmed-but-*unattributed* money — T10's `UNMATCHED` queue — a different problem: `INVESTOR_CASH` is confirmed and attributed, just not yet committed to a contract).

Making those two decisions concrete surfaced two structural defects in the ledger's existing convention that block any correct `FUNDING` posting. This spec closes both, gives the complete leg table for every money-movement event, and states the reconciliation invariant that ties the ledger to the bank statement. **This is a spec, not an implementation** — no code in `app/payments/`, `app/ledger/`, or a new migration is written against it here.

---

## 2. Out of Scope

- **Bank integration itself** — the Brankas/direct-bank client, `inbound_transfer` matching, the `UNMATCHED` queue, statement import. That is T10's job; this spec gives T10 the leg table to post once a movement is matched, and states the invariant T10's reconciliation must preserve.
- **The `FEE` rate, its config, and per-installment principal/interest split arithmetic.** That is T14 ("Repayment split and the `FEE` leg"). This spec fixes the shape T14's legs must produce (§6.3) and the account they must additionally touch (`UNEARNED_INTEREST`, §3), but not the split percentages or config surface.
- **Compliance/exposure-cap enforcement, share conversion, Decree 94 reporting.**
- **Escrow-mode custodial accounts.** Every leg table below is written against the omnibus-first path (`resolve_custodial_account` returns the single `PLATFORM` account); nothing here is incompatible with the escrow seam, but the escrow migration trigger is out of scope (ledger-foundation Open Q#3).
- **Order/listing/contract state-machine rewiring (Issue 10).** T10 makes `funded_amount`/`FUNDED`/`ACTIVE_FUNDED` move only on a confirmed `FUNDING` posting instead of order placement. This spec defines the `FUNDING` leg that confirmation posts; the guard rewiring itself is T10.

---

## 3. Data Model

### 3.1 New `ledger_accounts.account_type` values

The foundation spec's chart of accounts (`OMNIBUS_CASH`, `LENDER`, `BORROWER`, `FL_REVENUE`, `SUSPENSE`) is extended with three new types. `account_type` carries a DB `CHECK` constraint — adding these is a migration, not just a code change.

```
INVESTOR_CASH     -- platform-level. owner_user_id SET, contract_id NULL.
                     An investor's confirmed-but-uncommitted cash: money FundLok has
                     received and knows belongs to this investor, but that has not yet
                     been applied to a specific contract's LENDER claim. NOT a SUSPENSE
                     use — SUSPENSE is for money we cannot yet attribute to anyone at all
                     (ledger-foundation Open Q#2; T10's UNMATCHED queue). INVESTOR_CASH is
                     the opposite: fully attributed, just not yet committed.

EXTERNAL          -- platform-level. owner_user_id NULL, contract_id NULL. Exactly one
                     row, seeded like the single PLATFORM custodial account's OMNIBUS_CASH
                     account. Represents "outside the ledger's perimeter" — the investor's
                     or borrower's own bank account, on the far side of the FBO boundary.
                     See §3.3 for why this is required and §6.1 for the rule governing it.

UNEARNED_INTEREST -- contract-scoped. owner_user_id NULL, contract_id SET. The interest
                     component of a facility's obligation that has been recognised against
                     the borrower at origination but not yet earned by collecting a
                     repayment. See §3.4 and §6.2 for why DISBURSEMENT needs this.
```

Updated constraint:

```sql
ALTER TABLE ledger_accounts DROP CONSTRAINT <existing_check_name>;
ALTER TABLE ledger_accounts ADD CONSTRAINT <name> CHECK (
  account_type IN ('OMNIBUS_CASH','LENDER','BORROWER','FL_REVENUE','SUSPENSE',
                    'INVESTOR_CASH','EXTERNAL','UNEARNED_INTEREST')
);
```

### 3.2 `ledger_entries.contract_id` becomes nullable

Today `ledger_entries.contract_id` is `NOT NULL` (ledger-foundation §3) and `LedgerLeg.contract_id` is a required (non-`Optional`) field. Both must change. An `INVESTOR_CASH` top-up or withdrawal (§6.4) happens **before any contract exists** — Issue 16's whole premise is that an investor can wire funds before choosing a deal — so it has no contract to declare.

```
LedgerLeg.contract_id: UUID | None = None      # was: UUID (required)
ledger_entries.contract_id: nullable=True      # was: nullable=False
```

New business rule replacing the old `NOT NULL` constraint (enforced in `post_transaction`, not a DB `CHECK`, since it requires a join to each leg's accounts): **`contract_id` may be `NULL` on a leg only if both of that leg's accounts have `contract_id IS NULL`** (i.e. both are platform-level: `OMNIBUS_CASH`, `INVESTOR_CASH`, `EXTERNAL`, `FL_REVENUE`, or `SUSPENSE`). The moment either account is `LENDER`, `BORROWER`, or `UNEARNED_INTEREST`, the leg — and the transaction — must declare that contract's id, exactly as today.

### 3.3 Why `EXTERNAL` is required — the boundary-crossing problem

Every `ledger_entries` row moves `amount` from one **internal** account to another (ledger-foundation §3: "each leg is a complete, self-balancing transfer"). `DISBURSEMENT` and `REPAYMENT` get away without a boundary account because their real-world cash movement and their internal position change are the *same fact wearing two hats*: money leaving the omnibus account to the borrower **is** the establishment of the borrower's obligation (a single leg, `OMNIBUS_CASH` debited / `BORROWER` credited, does both at once — one side of the pair moves toward the cash pool, the other away from it).

`FUNDING` cannot be expressed that way. When an investor's wire lands, **two** internal balances must increase at once: `OMNIBUS_CASH` (the bank really did receive cash) and `LENDER` or `INVESTOR_CASH` (the investor's recorded claim/holding really did grow). A single leg can only increase one side and decrease the other — it cannot credit two accounts in one row. There is no existing account willing to be *decreased* to balance the credit to `OMNIBUS_CASH`, because the money did not come from anywhere internal — it came from outside the ledger's whole perimeter. That is Issue 16's "investor cash arriving from outside has nothing to move from," restated precisely.

**Resolution: `EXTERNAL`**, a single platform-level account standing in for "the rest of the world" (an investor's own bank account, a borrower's own bank account — whichever real account is on the far side of a given wire). It is deliberately not `OMNIBUS_CASH`-as-its-own-contra: `OMNIBUS_CASH`'s balance is the platform's central reconciliation anchor (§6.5) and must move by exactly the amount of each real bank movement and nothing else; letting it debit and credit itself either breaks `post_transaction` (`debit_account_id == credit_account_id` is rejected outright) or requires fabricating a second phantom leg that has no economic referent.

Every `FUNDING` and withdrawal event is therefore **two legs in one transaction**, with `OMNIBUS_CASH` as the pass-through hub (ledger-foundation's own account of the pass-through invariant, from `post_transaction`'s docstring, already covers exactly this shape — see §6.1):

```
leg 1: debit EXTERNAL          credit OMNIBUS_CASH        -- real cash enters the bank
leg 2: debit OMNIBUS_CASH      credit LENDER|INVESTOR_CASH -- internal claim established
```

`OMNIBUS_CASH` is touched twice and nets to zero (+amount then −amount) — it is a genuine hub, not an endpoint, exactly the case the foundation spec's pass-through check exists for. `EXTERNAL` and `LENDER`/`INVESTOR_CASH` are each touched once — genuine economic endpoints.

### 3.4 Why `UNEARNED_INTEREST` is required — the `T₀`-at-origination problem

HANDOFF-03 §5.2, defect 1: `DISBURSEMENT` today credits `BORROWER` with `P` only, but repayments debit it with `T = P + I` over the facility's life, so a fully-repaid, healthy loan leaves `BORROWER` at `P − T = −I` forever — a non-zero "balance" on an account that should net to zero the moment the debt is settled. **Fix, per the resolution: recognise the full obligation `T₀` at origination.** This is sound specifically because S4 fixes `T₀` at origination with flat interest and no re-amortisation (repayment-schedule spec, D-series decisions) — `T₀` is known, fixed, and immutable from day one, so there is nothing provisional about crediting it in full immediately.

But only `P` actually leaves the bank at disbursement. Crediting `BORROWER` with `T₀` in the same single leg that debits `OMNIBUS_CASH` would overstate the real cash outflow by `I₀ = T₀ − P` and break the reconciliation invariant (§6.5) on day one of every facility. The extra `I₀` is not cash — it is the borrower's committed future interest cost, which will only become real money as repayments arrive over the life of the loan.

**Resolution: `UNEARNED_INTEREST`**, one contract-scoped account per facility, debited `I₀` at origination (going negative — this is intentional: it represents interest FundLok has recognised as owed but not yet collected) and credited back up toward zero by the interest portion of every subsequent repayment (T14's job; see §6.3). At full, on-schedule repayment its balance returns to exactly `0`.

```
leg 1 (real cash):        debit OMNIBUS_CASH        credit BORROWER            amount = P
leg 2 (deferred interest): debit UNEARNED_INTEREST    credit BORROWER            amount = I₀ = T₀ − P
```

`BORROWER` is touched twice **as a pure multi-source recipient** (credited by both legs, never debited within this transaction) — see the important implementation note in §6.1 about why this is *not* the same shape as a pass-through hub, and why it currently would incorrectly trip `post_transaction`'s net-zero check.

### 3.5 Account summary

| account_type | Scope | owner_user_id | contract_id | Meaning |
|---|---|---|---|---|
| `OMNIBUS_CASH` | Platform | NULL | NULL | The bank's actual cash position (unchanged). |
| `LENDER` | Contract | investor | contract | Investor's **outstanding claim** on this contract (redefined, Issue 15). |
| `BORROWER` | Contract | — | contract | Borrower's **outstanding obligation** `T₀`, drawn down to 0 by repayments (redefined, defect 1). |
| `FL_REVENUE` | Platform | NULL | NULL | FL's collected fee revenue (unchanged). |
| `SUSPENSE` | Platform | NULL | NULL | Confirmed-but-**unattributed** funds (unchanged; still no handling logic built, ledger-foundation Open Q#2). |
| `INVESTOR_CASH` | Platform | investor | NULL | Confirmed-and-attributed, **uncommitted** investor cash (new, Issue 16). |
| `EXTERNAL` | Platform | NULL | NULL | The far side of the FBO boundary — one row, seeded once (new, defect 2). |
| `UNEARNED_INTEREST` | Contract | NULL | contract | Interest recognised at origination but not yet earned (new, defect 1). |

---

## 4. API Contract

Like the foundation it builds on, this spec defines **internal service functions** in `app/payments/service.py` (rewritten, not the current shim). The HTTP endpoints that call them (`POST /payments/*`, order confirmation) are T10's — this is the contract T10 builds against.

```python
# app/payments/service.py — all async, all AsyncSession

async def record_funding(
    db: AsyncSession, *,
    investor_id: UUID,
    amount: Decimal,
    contract_id: UUID | None,       # None => lands in INVESTOR_CASH, uncommitted
    idempotency_key: str,           # T10: the bank's own payment_reference, not client-supplied
    reference: str | None = None,
    created_by: UUID | None = None,
) -> LedgerTransaction:
    """Posts the 2-leg EXTERNAL -> OMNIBUS_CASH -> {LENDER|INVESTOR_CASH} transaction (§3.3,
    §6.1). Raises if contract_id is given but the contract has no INVESTOR_CASH-eligible
    state, or if amount <= 0."""

async def commit_investor_cash(
    db: AsyncSession, *,
    investor_id: UUID,
    contract_id: UUID,
    amount: Decimal,
    idempotency_key: str,
    created_by: UUID | None = None,
) -> LedgerTransaction:
    """Applies previously-uncommitted INVESTOR_CASH to a specific contract's LENDER claim.
    Single leg (no bank crossing): debit INVESTOR_CASH, credit LENDER, type FUNDING.
    Raises if the investor's INVESTOR_CASH balance is less than amount."""

async def record_withdrawal(
    db: AsyncSession, *,
    investor_id: UUID,
    amount: Decimal,
    idempotency_key: str,
    created_by: UUID | None = None,
) -> LedgerTransaction:
    """Returns uncommitted INVESTOR_CASH to the investor's real bank account. 2-leg,
    mirror of record_funding (§6.4), type REFUND. Raises if amount exceeds the investor's
    INVESTOR_CASH balance."""

async def record_disbursement(
    db: AsyncSession, *,
    contract_id: UUID,
    bank_account: str,
    principal_amount: Decimal,      # P — the real wire amount
    total_obligation_amount: Decimal,  # T0 — from the repayment schedule (T7's output)
    idempotency_key: str | None,
    created_by: UUID,
) -> LedgerTransaction:
    """2-leg: real-cash leg (OMNIBUS_CASH/BORROWER, amount=P) + deferred-interest leg
    (UNEARNED_INTEREST/BORROWER, amount=T0-P) per §3.4/§6.2. Signature changes from today's
    single `amount` param — callers must supply both P and T0 explicitly; T0 must equal the
    repayment schedule's T0 (INV-5) byte-for-byte, never re-derived here."""

async def record_repayment(
    db: AsyncSession, *,
    contract_id: UUID,
    amount: Decimal,
    principal_component: Decimal,
    interest_component: Decimal,    # T14's split; principal_component + interest_component == amount
    fee_component: Decimal,         # may be 0; omit the FEE leg entirely when it is (T14)
    paid_at: datetime,
    reference: str | None,
    idempotency_key: str | None,
    created_by: UUID,
) -> LedgerTransaction:
    """Rewritten for T14: REPAYMENT leg (BORROWER/OMNIBUS_CASH, amount=amount, unchanged from
    today) + an UNEARNED_INTEREST-recognition leg (OMNIBUS_CASH/UNEARNED_INTEREST is wrong
    direction -- see §6.3 for the exact leg) + per-holding DISTRIBUTION legs, now DEBITING
    LENDER (Issue 15, reversed from today) + an optional FEE leg to FL_REVENUE."""
```

No new public HTTP write surface is defined here — `Idempotency-Key` handling is unchanged from the foundation spec (event-level, via `ledger_transactions.idempotency_key`), except that for bank-matched events (`FUNDING`, `record_withdrawal`) the key **is the bank's own transaction reference**, never client-supplied (T10 §"Matching," already decided: "Idempotent on the bank's own reference, not a client-supplied key").

---

## 5. State Machine

Not applicable to the ledger legs themselves (ledger rows are immutable facts, per the foundation spec). This spec does, however, fix the **trigger condition** T10 must implement for Issue 10: `listing.funded_amount`/`contract.funded_amount` increment, and `listing.status="FUNDED"`/`contract.status="ACTIVE_FUNDED"` transition, **only** on a successfully posted `FUNDING` transaction that commits to that contract (`commit_investor_cash` or a direct `record_funding(..., contract_id=...)`) — never on order placement. That rewiring itself belongs to T10; this spec supplies the leg that must exist before the state can legitimately move.

---

## 6. Business Rules

### 6.1 The full leg table

| Event | Type | Leg 1 | Leg 2 | Leg 3+ |
|---|---|---|---|---|
| Investor wires funds, uncommitted | `FUNDING` | debit `EXTERNAL` / credit `OMNIBUS_CASH`, amount | debit `OMNIBUS_CASH` / credit `INVESTOR_CASH`, amount | — |
| Investor wires funds, direct to a chosen contract | `FUNDING` | debit `EXTERNAL` / credit `OMNIBUS_CASH`, amount | debit `OMNIBUS_CASH` / credit `LENDER`, amount | — |
| Investor commits existing `INVESTOR_CASH` to a contract | `FUNDING` | debit `INVESTOR_CASH` / credit `LENDER`, amount | — | — |
| Investor withdraws uncommitted `INVESTOR_CASH` | `REFUND` | debit `INVESTOR_CASH` / credit `OMNIBUS_CASH`, amount | debit `OMNIBUS_CASH` / credit `EXTERNAL`, amount | — |
| Disbursement | `DISBURSEMENT` | debit `OMNIBUS_CASH` / credit `BORROWER`, amount=`P` | debit `UNEARNED_INTEREST` / credit `BORROWER`, amount=`T0-P` | — |
| Repayment (installment) | `REPAYMENT` | debit `BORROWER` / credit `OMNIBUS_CASH`, amount | — | — |
| Repayment — interest recognition | `REPAYMENT` | debit `UNEARNED_INTEREST`... **see note below** | | |
| Distribution (per holding, principal component) | `DISTRIBUTION` | debit `LENDER` / credit `OMNIBUS_CASH`, amount | — | — |
| Fee (if rate > 0) | `FEE` | debit `OMNIBUS_CASH` / credit `FL_REVENUE`, amount | — | — |

**Note on "Repayment — interest recognition":** this is *not* a new leg against `OMNIBUS_CASH` — the cash side of the repayment is already fully captured by the single `REPAYMENT` leg above. What must happen is that `UNEARNED_INTEREST`'s balance moves back toward zero by exactly this installment's interest component, and the natural, ledger-consistent way to express "an account's balance moves without cash moving" is a leg **within** the same multi-leg transaction that has another *already-present* endpoint as its counterpart. `BORROWER` is that counterpart: the single `REPAYMENT` leg above debits `BORROWER` by the **full** installment (`amount = principal + interest`, unchanged from today), which already accounts for retiring both the principal and interest portions of `T₀`. `UNEARNED_INTEREST` is credited back up by the interest portion **against `BORROWER`** as a second, purely-internal leg:

```
leg (type REPAYMENT): debit BORROWER    credit UNEARNED_INTEREST    amount = interest_component
```

This makes `BORROWER` touched twice within the repayment transaction (debited the full installment by leg 1, credited the interest component by this leg) — net = `-(principal+interest) + interest = -principal`, which is correct: the loan's `BORROWER` claim should shrink by exactly the principal component per installment once the interest side is squared away against `UNEARNED_INTEREST`, and by full repayment `BORROWER` reaches `0` and `UNEARNED_INTEREST` also reaches `0` (it was debited `I₀` once at origination and credited back the sum of every installment's interest component, which totals `I₀` by construction of the repayment schedule).

**Implementation note for T10/T14 (not applicable to this spec's own scope, since T21 is spec-only, but must be fixed before either task can post a real transaction):** `post_transaction`'s pass-through check (`app/ledger/service.py`) currently treats **any** account touched by more than one leg in a transaction as a hub that must net to zero. That is correct for `OMNIBUS_CASH` in the `FUNDING`/withdrawal legs above (§3.3) — money genuinely passes through it. It is **not** correct for `BORROWER` in the `DISBURSEMENT` and `REPAYMENT`-interest-recognition legs above: `BORROWER` is a pure multi-source **endpoint** there (credited by two unrelated legs at disbursement; debited once and credited once at repayment, netting to `-principal`, not `0`). Both are legitimate and must not raise `LedgerImbalanceError`. The check must be narrowed from "touched more than once ⇒ net to zero" to "touched on **both** its debit side and its credit side within the same transaction by legs that are economically a single pass-through flow ⇒ net to zero" — concretely, `OMNIBUS_CASH` qualifies (it is the debit side of one leg and the credit side of another, same amount flowing through); `BORROWER` in the disbursement case does not (it is only ever the credit side, from two different sources) and must be exempted regardless of touch count. T10 must fix this before `record_disbursement` above can run without raising.

### 6.2 Disbursement recognises `T₀`, not `P`

`record_disbursement` must be called with the repayment schedule's actual `T₀` (T7's `origination.py` output), never a value re-derived in `app/payments/`. `T₀` and `P` disagreeing between the schedule and the ledger is a data-integrity bug, not a ledger concern — `record_disbursement` should assert `T0 >= P` and raise (not silently clamp) if the caller ever passes `T0 < P` or `T0 == P` (zero interest is a schedule anomaly, not a payments-layer decision).

### 6.3 T14 must additionally touch `UNEARNED_INTEREST`

T14's repayment-split rewrite of `record_repayment` produces, per installment: the unchanged `REPAYMENT` leg (§6.1), the `BORROWER`/`UNEARNED_INTEREST` interest-recognition leg (§6.1 note), the per-holding `DISTRIBUTION` legs (now **debiting** `LENDER`, §6.4), and an optional `FEE` leg. `principal_component + interest_component` must equal the installment `amount` exactly (integer VND, largest-remainder splitter per T1 — same technique already used for the `DISTRIBUTION` apportionment in today's shim).

### 6.4 `DISTRIBUTION` debits `LENDER` (Issue 15, reversed)

Today's shim credits `LENDER` on `DISTRIBUTION`. Per the resolution, `LENDER` represents the outstanding claim, so paying it down is a **debit**:

```
leg (type DISTRIBUTION): debit LENDER    credit OMNIBUS_CASH    amount = holding's share
```

`LENDER`'s balance is established (credited) once, at `FUNDING` (§6.1), and drawn down (debited) by every subsequent `DISTRIBUTION` — mirroring `BORROWER` exactly, which gives a real invariant worth asserting (§8): summed over a contract, `Balance(BORROWER) + Σ Balance(LENDER_i)` should track a consistent relationship throughout the facility's life (both sides of the same contract, moving in lockstep as the obligation is paid down and the claims are satisfied).

### 6.5 The reconciliation invariant

**INV-R1 (bank reconciliation).** At any point in time, `Balance(OMNIBUS_CASH)` — `SUM(credits) − SUM(debits)` over `ledger_entries`, exactly as `get_account_balance` already computes it — must equal the omnibus custodial account's actual bank statement balance. Every `ledger_entries` row that touches `OMNIBUS_CASH` corresponds to one real, bank-visible movement: either a boundary-crossing leg (`FUNDING`/withdrawal, via `EXTERNAL`, §3.3) not yet tied to a specific contract's obligation, or a `DISBURSEMENT`/`REPAYMENT` leg that is simultaneously a boundary crossing *and* the establishment or reduction of a specific contract's obligation (§3.3's "same fact wearing two hats"). No `ledger_entries` row may touch `OMNIBUS_CASH` without a corresponding real bank transaction, and — this is what T10's `inbound_transfer` matching and manual disbursement recording jointly guarantee — no real bank transaction may occur without eventually producing a corresponding `ledger_entries` row.

**INV-R2 (boundary discipline).** Every `ledger_entries` row where either `debit_account` or `credit_account` has `account_type = 'EXTERNAL'` has the *other* account of type `OMNIBUS_CASH`. `EXTERNAL` never appears opposite any other account type. This is enforced by convention in the service functions above (§4), not a DB constraint (the ledger schema does not carry per-row account-type checks).

**INV-R3 (unearned interest unwinds to zero).** For a contract that reaches full, on-schedule repayment, `Balance(UNEARNED_INTEREST)` for that contract returns to exactly `0`: debited `I₀ = T₀ − P` once at origination (§3.4), credited back the sum of every installment's `interest_component` (§6.3), and by construction of the repayment schedule those interest components sum to exactly `I₀`.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| `record_funding`/`record_withdrawal` called with `amount <= 0` | Nothing written; `post_transaction` raises `LedgerImbalanceError` (leg amount must be positive) | 422 |
| `commit_investor_cash` requests more than the investor's current `INVESTOR_CASH` balance | Service checks `get_account_balance` before posting; raises `InsufficientInvestorCashError` (new) | 409 |
| `record_withdrawal` requests more than the investor's `INVESTOR_CASH` balance | Same as above | 409 |
| `record_disbursement` called with `total_obligation_amount < principal_amount` | Service raises `InvalidObligationError` (new) before any leg is built — this is a caller bug (T7 schedule mismatch), not a normal error path | 500 (should never be reachable from correct callers) |
| `record_repayment`'s `principal_component + interest_component + fee_component != amount` | Service raises `LedgerImbalanceError`-style validation before calling `post_transaction` (the legs would not balance) | 422 |
| Zero-rate fee on a repayment | `FEE` leg omitted entirely (T14, unchanged from HANDOFF-03 §3's instruction) — never a zero-amount leg | N/A, not an error |
| A `FUNDING`/withdrawal leg is built with a non-NULL `contract_id` on an account that is actually platform-level, or vice versa | `post_transaction`'s widened contract-consistency check (§3.2) raises `CrossContractTransactionError` | 422 |
| Replayed bank `payment_reference` (idempotency key) for `FUNDING` | Return existing transaction, write nothing (foundation spec, unchanged) | Existing transaction returned |

---

## 8. Acceptance Criteria

- [ ] `test_funding_uncommitted_credits_investor_cash_via_external` — a `record_funding(contract_id=None)` call posts exactly 2 legs; `EXTERNAL` and `INVESTOR_CASH` are each touched once; `OMNIBUS_CASH` nets to zero within the transaction.
- [ ] `test_funding_direct_to_contract_credits_lender` — `record_funding(contract_id=...)` posts `EXTERNAL -> OMNIBUS_CASH -> LENDER`; `LENDER`'s balance increases by the funded amount.
- [ ] `test_commit_investor_cash_moves_investor_cash_to_lender_with_no_bank_leg` — a single-leg transaction; `OMNIBUS_CASH` and `EXTERNAL` are untouched.
- [ ] `test_commit_investor_cash_rejects_amount_exceeding_balance` — raises before writing anything.
- [ ] `test_withdrawal_mirrors_funding_through_external` — `INVESTOR_CASH -> OMNIBUS_CASH -> EXTERNAL`; `OMNIBUS_CASH` nets to zero.
- [ ] `test_disbursement_posts_two_legs_p_and_deferred_interest` — `BORROWER`'s resulting balance equals `T0` exactly; `OMNIBUS_CASH` decreases by exactly `P` (not `T0`); `UNEARNED_INTEREST` decreases by exactly `I0`.
- [ ] `test_borrower_settles_at_exactly_zero_after_full_repayment` — regression test for defect 1: simulate a full repayment schedule; `Balance(BORROWER) == 0` at the end, not `-I`.
- [ ] `test_unearned_interest_unwinds_to_zero_on_full_repayment` — INV-R3, end to end.
- [ ] `test_distribution_debits_lender_not_credits` — regression test for Issue 15's reversal; `LENDER`'s balance decreases by the distributed share.
- [ ] `test_lender_credited_at_funding_debited_at_distribution_nets_to_zero_at_full_payout` — a fully-repaid contract's `LENDER` balance for each holding returns to `0`.
- [ ] `test_fee_leg_omitted_at_zero_rate_no_zero_amount_leg_attempted` — carried over from T14's acceptance criteria, verified again here against the new leg shape.
- [ ] `test_ledger_entries_contract_id_nullable_for_platform_only_legs` — a `FUNDING`-to-`INVESTOR_CASH` transaction's legs persist with `contract_id IS NULL`.
- [ ] `test_ledger_entries_contract_id_still_required_when_either_account_is_contract_scoped` — a `LENDER`/`BORROWER`/`UNEARNED_INTEREST`-touching leg with `contract_id=None` is rejected.
- [ ] `test_external_never_appears_opposite_a_non_omnibus_account` — INV-R2, asserted as a service-layer invariant test, not a DB constraint test.
- [ ] `test_reconciliation_omnibus_balance_matches_sum_of_all_boundary_crossings` — INV-R1: sum every `EXTERNAL`-touching and direct `BORROWER`-cash-touching leg's signed effect on `OMNIBUS_CASH`; assert it equals `get_account_balance(omnibus_cash_id)`.

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Does `UNEARNED_INTEREST` need its own row per contract seeded proactively, or created lazily by `get_or_create_account` on first disbursement (like every other account today)? | Edward | **RESOLVED** — lazily, via `get_or_create_account`, exactly like every other contract-scoped account. No proactive seeding; consistent with the rest of the chart of accounts. |
| 2 | Should `post_transaction`'s pass-through check be fixed in this spec's implementation, or left to T10? | Edward | **RESOLVED** — left to T10/T14 (§6.1's implementation note). This spec's job is to specify the correct leg shapes and name the exact defect in the current check; fixing `app/ledger/service.py` is implementation, out of this spec's scope per its own header. |
| 3 | Can an investor's `INVESTOR_CASH` ever go negative (e.g. a withdrawal race with a concurrent commit)? | Edward | **OPEN** — `commit_investor_cash`/`record_withdrawal`'s balance check (§7) is a read-then-write check with no row lock specified here. T10 must decide whether this needs `SELECT FOR UPDATE` on the `INVESTOR_CASH` account's postings or an application-level serialization per investor, the same class of problem the ledger-foundation spec left to the disbursement flow's row lock (foundation spec §2, "Out of Scope"). Not resolved here because it is a concurrency-control decision for T10's endpoints, not a leg-shape decision. |
| 4 | Does `EXTERNAL` ever need to be contract-scoped (e.g. to reconcile a specific investor's wire against a specific expected amount) instead of one platform-level row? | Edward | **RESOLVED** — no. `EXTERNAL` is a pure boundary-crossing abstraction, not a party account; per-investor/per-contract attribution already happens via the *other* leg of the same transaction (`INVESTOR_CASH`/`LENDER`/`BORROWER`, all of which already carry `owner_user_id`/`contract_id`). A second, contract-scoped `EXTERNAL` account per contract would duplicate that attribution for no benefit and would multiply the accounts T10's reconciliation tooling has to sum over. |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial spec — full leg table for FUNDING, DISBURSEMENT, REPAYMENT, DISTRIBUTION, FEE and withdrawal per HANDOFF-03 §5.2 (T0f); introduces `INVESTOR_CASH` (Issue 16), `EXTERNAL` (defect 2), and `UNEARNED_INTEREST` (defect 1); reverses `DISTRIBUTION` to debit `LENDER` (Issue 15); states the bank-statement reconciliation invariant (INV-R1–R3); flags the `post_transaction` pass-through-check narrowing T10/T14 must make before either can post a real transaction. ACCEPTED — cleared to unblock T10 and T14. |
