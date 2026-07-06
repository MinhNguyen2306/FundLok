# ADR-003: Omnibus-First with an Escrow-Compatible Ledger Seam

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | July 2026 |
| **Deciders** | Edward Wong (CTO) |
| **Supersedes** | Refines ADR-002 (does not replace it) |

## Context

ADR-002 committed FundLok to an omnibus/custodial account model. Since then two facts have changed the picture:

1. **No custodial banking partner is signed yet.** The CEO has indicated some Vietnamese institutions — typically the more conservative ones — will only offer a **per-project escrow** account rather than a single pooled omnibus account. We may be forced into escrow by whichever partner we can actually sign.
2. **We do not want to block V2 ledger work on that commercial decision.**

In the escrow model, each account holds exactly **one SME (borrower) and its one-to-many lenders**, FL retains management control and can deduct its revenue %. In the omnibus model, a **single** pooled account holds funds for every project at once.

The two models differ in exactly one dimension: **account topology.** Everything else — the immutable double-entry ledger, per-contract and per-lender balances, the `SELECT FOR UPDATE` disbursement lock (see the team deck), the FEE posting that deducts FL revenue — is identical.

## Decision

**Implement omnibus now. Build every ledger and money-movement structure behind a `custodial_account` indirection so that switching to escrow is a data migration, not a rewrite.**

Concretely:

- A `custodial_account` represents one physical bank account. It has a **scope**:
  - `PLATFORM` — the single pooled account (omnibus). Exactly one row.
  - `CONTRACT` — one account per contract (escrow). One row per contract, carrying `contract_id`.
- Every internal ledger account and every (future) `bank_transaction` references a `custodial_account`. Nothing references "the omnibus account" as a global singleton.
- **Omnibus is the special case of escrow where all logical accounts map onto one `PLATFORM` custodial account.** Escrow is the case where they map onto N `CONTRACT` accounts.

Switching omnibus → escrow later becomes: create N `CONTRACT` custodial accounts, remap each contract's ledger accounts to its own custodial account, and make reconciliation per-account. It is a migration + a remap, not a ledger redesign.

## The one invariant that keeps the seam cheap

**No platform-wide netting.** The ledger must never assume it can move value between projects or compute a single global balance as an economic truth. Each contract's funds are logically ring-fenced from day one, even under omnibus where they physically share one bank account. Any code that nets across contracts (e.g. "the platform has $X, disburse from the pool") is an omnibus-only convenience that would break the escrow swap — and is undesirable regardless, because it blurs whose money is whose.

## Consequences

- The ledger foundation spec (`docs/specs/ledger/ledger-foundation.md`) introduces `custodial_accounts` and a `ledger_accounts` chart-of-accounts keyed to them from the start, even though only one `PLATFORM` custodial account exists at launch.
- ADR-002 stays as written: partner still TBD, Brankas-or-direct still open. This ADR only fixes the *internal* modeling so either commercial outcome is absorbable.
- A future ADR will record the actual custodial partner and whether we launched omnibus or were forced to escrow. If escrow, it will reference the migration that provisions per-contract accounts.
- Slightly more upfront modeling (an account layer that is "trivial" under omnibus) in exchange for making a plausible, partner-driven pivot cheap. Given the partner is unsigned, this is cheap insurance.

## Rationale

- The existing `ledger_entries` table is already scoped by `contract_id`, so per-contract ring-fencing is a natural fit — escrow's "one account per contract" maps onto structure we already have.
- Deferring the omnibus-vs-escrow commercial decision without deferring engineering keeps V2 on schedule.
- The alternative — build omnibus with a hard-coded single pool, then rework the ledger if forced to escrow — risks a costly rewrite of the most correctness-sensitive part of the system (the money ledger) under time pressure.
