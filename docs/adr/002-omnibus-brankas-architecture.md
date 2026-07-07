# ADR-002: Omnibus/Custodial Account via Brankas

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | June 2026 |
| **Deciders** | Edward Wong (CTO) |

## Context

FundLok must move real money between lenders, borrowers, and FL as the platform operator. FL is not a licensed bank and cannot hold customer funds directly. A regulated structure is required under Vietnam Decree 94/2025/ND-CP.

## Decision

FL opens a single omnibus (custodial) account at a licensed Vietnamese bank. All fund movements flow through this account. Brankas (or equivalent Vietnam-registered Open API aggregator) mediates every inbound and outbound payment between the omnibus account and end-user bank accounts.

FL maintains an internal append-only ledger that mirrors every movement. The ledger is the legal record.

## Money Flow

```
Lender          → [Brankas inbound]  → FL Omnibus Account  → ledger: FUNDING
Borrower        → [Brankas inbound]  → FL Omnibus Account  → ledger: REPAYMENT
FL Omnibus Acct → [Brankas outbound] → Borrower            → ledger: DISBURSEMENT
FL Omnibus Acct → [Brankas outbound] → Lender              → ledger: DISTRIBUTION
FL Omnibus Acct → [internal]         → FL Revenue           → ledger: FEE
```

## Ledger Immutability

The `ledger_entries` table is append-only. Enforced at:
- Application layer: no UPDATE or DELETE calls in service code
- Database layer: PostgreSQL trigger blocks UPDATE/DELETE (migration 0006)

Corrections are made by adding new entries, never by modifying existing ones.

## New Tables

- `bank_transactions` — links each `ledger_entry` to a Brankas `transaction_id`, direction, and settlement status
- `omnibus_balance_snapshots` — periodic point-in-time balance snapshots for reconciliation and Decree 94 reporting

## Rationale

- Omnibus structure is the standard P2P lending architecture in SEA regulated markets
- Brankas provides a standardised API abstracting away individual Vietnamese bank APIs
- The existing idempotency key pattern on `orders` and `ledger_entries` is exactly the webhook safety mechanism Brankas requires — no rework needed
- Append-only ledger is already the MVP's pattern — only the DB-level trigger is new

## Consequences

- All financial operations are async: initiation is synchronous, settlement is confirmed via Brankas webhook
- API responses for financial endpoints use 202 Accepted, not 201 Created
- No direct database writes for financial events without a corresponding `bank_transaction` record (except legacy admin operations during Phase 0)
- Brankas webhook endpoint must be publicly reachable and HMAC-validated

## Update — July 2026: Vietnam Access & Partner Status

- **Brankas does not serve Vietnam directly.** In Vietnam it operates through a local partner,
  **Gimasys** (https://gimasys.com/). Edward has reached out to Gimasys to explore their services.
- **Preferred end state:** integrate directly with the custodial bank whose Open API can span the
  banks and e-wallets of FL's borrowers and lenders (via NAPAS interoperability), rather than
  carrying a separate aggregator. This also satisfies Decree 94's requirement to settle through
  bank accounts or licensed e-wallets (see ADR-004).
- **Decision still open** between (a) aggregator via Gimasys/Brankas and (b) direct custodial-bank
  Open API. Per ADR-003, `app/banking/` is built bank-agnostic (client behind an interface), so
  this is a swappable implementation, not an architecture change.
- **Integration work is deferred** until a custodial banking partner is signed. The ledger
  foundation (ADR-003) and compliance work (ADR-004) are intentionally partner-agnostic so they
  are not blocked by this decision.
