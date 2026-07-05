# Spec: Brankas Loan Disbursement

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/banking/` |
| **Version** | 1.0 |
| **Date** | June 2026 |
| **Related ADR** | ADR-002 (Omnibus/Brankas Architecture) |
| **Depends on** | Contract must be `ACTIVE_FUNDED`; Listing must be `FUNDED` |

---

## 1. Context & Goal

When a loan listing reaches its funding target, FL must disburse the raised capital to the borrower's registered bank account. In V1 this was a manual admin ledger write with no actual bank movement. In V2, the disbursement triggers a real outbound payment via Brankas from the FL omnibus account to the borrower.

**Goal:** Replace the manual disbursement ledger write with a Brankas-mediated outbound payment that writes to both `bank_transactions` and `ledger_entries`, and handles async settlement via Brankas webhook.

---

## 2. Out of Scope

- Lender funding inflows (separate spec: `banking/brankas-investor-funding.md`)
- Borrower repayment inflows (separate spec: `banking/brankas-repayment.md`)
- Fee deduction logic (handled as part of disbursement distribution — separate spec)
- Partial disbursement (V2 disburses full funded amount in one transaction)
- Brankas account onboarding / omnibus account setup (ops task, not code)

---

## 3. Data Model

### New Table: `bank_transactions`

```
bank_transactions
├── id                    UUID          PK, default gen_random_uuid()
├── ledger_entry_id       UUID          NOT NULL → references ledger_entries(id) ON DELETE RESTRICT
├── brankas_transaction_id TEXT         UNIQUE, nullable (null until Brankas confirms)
├── bank_reference        TEXT          nullable (bank's own reference number, from Brankas)
├── direction             TEXT          NOT NULL, CHECK IN ('INBOUND', 'OUTBOUND')
├── status                TEXT          NOT NULL DEFAULT 'PENDING'
│                                         CHECK IN ('PENDING', 'SETTLED', 'FAILED', 'REVERSED')
├── amount                DECIMAL(15,2) NOT NULL
├── currency              TEXT          NOT NULL DEFAULT 'VND'
├── counterparty_account  TEXT          NOT NULL  -- borrower/lender bank account number
├── counterparty_name     TEXT          nullable
├── failure_reason        TEXT          nullable  -- populated on FAILED status
├── settled_at            TIMESTAMPTZ   nullable
├── created_at            TIMESTAMPTZ   DEFAULT NOW()
└── updated_at            TIMESTAMPTZ   DEFAULT NOW()
```

### New Table: `omnibus_balance_snapshots`

```
omnibus_balance_snapshots
├── id              UUID          PK, default gen_random_uuid()
├── balance         DECIMAL(15,2) NOT NULL
├── currency        TEXT          NOT NULL DEFAULT 'VND'
├── source          TEXT          NOT NULL CHECK IN ('BRANKAS_POLL', 'BRANKAS_WEBHOOK', 'MANUAL')
├── snapshotted_at  TIMESTAMPTZ   NOT NULL
└── created_at      TIMESTAMPTZ   DEFAULT NOW()
```

### Modified Table: `ledger_entries`

```
+ brankas_initiated   BOOLEAN  NOT NULL DEFAULT FALSE
  -- TRUE if this entry was triggered by a Brankas payment, FALSE if manually recorded (legacy/admin)
```

### Alembic Migration

`alembic/versions/0006_banking_tables.py`

---

## 4. API Contract

### `POST /payments/disbursements` *(existing endpoint — modified)*

The existing endpoint currently writes a ledger entry directly. In V2 it instead initiates a Brankas outbound payment. The ledger entry is written only after Brankas confirms initiation.

**Auth:** Bearer JWT — role: `ADMIN` only

**Request** *(unchanged from V1)*
```json
{
  "contract_id": "uuid",
  "bank_account": "string",   // borrower's registered bank account number
  "amount": "decimal string"  // e.g. "50000000.00" (VND)
}
```

**Headers**
```
Idempotency-Key: <uuid>   // required
```

**Response 202** *(changed from 201 — disbursement is now async)*
```json
{
  "disbursement_id": "uuid",        // ledger_entry.id
  "bank_transaction_id": "uuid",    // bank_transactions.id
  "brankas_transaction_id": "string | null",  // null until Brankas confirms initiation
  "status": "PENDING",
  "message": "Disbursement initiated. Settlement is asynchronous."
}
```

**Error Responses**

| Status | Condition |
|---|---|
| 400 | amount ≤ 0 |
| 400 | Contract not `ACTIVE_FUNDED` |
| 400 | Listing not `FUNDED` or funded_amount < target_amount |
| 400 | Disbursement already initiated for this contract (check ledger for existing DISBURSEMENT) |
| 404 | Contract not found |
| 409 | Idempotency-Key used for a different contract |
| 502 | Brankas API call failed (log and return — do NOT write ledger entry on Brankas failure) |

---

### `POST /webhooks/brankas` *(new endpoint)*

Brankas POSTs here when a payment status changes. This endpoint must be publicly reachable (no auth JWT) but must validate the Brankas webhook signature.

**Auth:** Brankas HMAC-SHA256 signature in `X-Brankas-Signature` header — validated against `BRANKAS_WEBHOOK_SECRET` env var. Return 401 if invalid.

**Request** *(Brankas standard webhook payload)*
```json
{
  "event": "payment.settled" | "payment.failed",
  "transaction_id": "string",   // Brankas transaction ID
  "reference": "string",        // FL's idempotency key, passed during initiation
  "amount": "decimal string",
  "currency": "VND",
  "settled_at": "ISO8601 timestamp | null",
  "failure_reason": "string | null"
}
```

**Response 200** *(always return 200 to Brankas — handle errors internally)*
```json
{ "received": true }
```

**Internal logic on `payment.settled`:**
1. Look up `bank_transactions` by `brankas_transaction_id`
2. If not found: look up by `reference` (idempotency key) — Brankas may call before initiation response returns
3. Update `bank_transaction.status = SETTLED`, set `settled_at`
4. Write `audit_log` entry
5. If type is DISBURSEMENT: emit `omnibus_balance_snapshot` (poll Brankas for current balance)

**Internal logic on `payment.failed`:**
1. Update `bank_transaction.status = FAILED`, set `failure_reason`
2. Write `audit_log` entry
3. Alert ops channel (email or notification — mechanism TBD)
4. Do NOT reverse the `ledger_entry` — write a new correcting entry if needed (immutable ledger rule)

---

## 5. State Machine

```
[Admin triggers POST /payments/disbursements]
        │
        ▼
bank_transaction: PENDING  ──────────────────────────────────────────────┐
ledger_entry: DISBURSEMENT (brankas_initiated=TRUE)                       │
        │                                                                  │
        ▼                                                                  ▼
[Brankas webhook: payment.settled]                         [Brankas webhook: payment.failed]
        │                                                                  │
        ▼                                                                  ▼
bank_transaction: SETTLED                                  bank_transaction: FAILED
ledger_entry: unchanged (immutable)                        ledger_entry: unchanged (immutable)
                                                           + new ledger_entry: CORRECTION (if needed)
```

**Who can trigger disbursement:** `ADMIN` role only.
**Invalid re-trigger:** If a `DISBURSEMENT` ledger entry already exists for a contract, return 400. One disbursement per contract.

---

## 6. Business Rules

1. A disbursement may only be initiated when `Contract.status == 'ACTIVE_FUNDED'` AND `Listing.status == 'FUNDED'` AND `Listing.funded_amount >= Listing.target_amount`.
2. The `ledger_entry` for a disbursement is written at initiation time (when Brankas accepts the payment request), not at settlement time. The `bank_transaction` record tracks the async settlement.
3. If Brankas returns an error on initiation (non-2xx), no `ledger_entry` or `bank_transaction` is written. The admin may retry.
4. The Brankas webhook endpoint must be idempotent — receiving the same `payment.settled` event twice must not create duplicate records or errors.
5. The disbursement amount must equal `Listing.funded_amount` minus FL's fee. Fee calculation is handled by the fee service (separate spec) — this spec assumes the amount passed in the request is already net of fee.
6. FL's omnibus account must have sufficient balance before initiating disbursement. Check via Brankas balance API before calling payment initiation. If insufficient: return 400 `INSUFFICIENT_OMNIBUS_BALANCE`.
7. All Brankas API calls must use the `Idempotency-Key` header. The same key passed to `POST /payments/disbursements` is forwarded to Brankas.

---

## 7. Error Cases

| Scenario | System behaviour | Response |
|---|---|---|
| Admin submits disbursement, Brankas returns 5xx | No ledger entry written. Log error. Return 502 to caller. Admin may retry with same Idempotency-Key. | 502 |
| Brankas webhook arrives before initiation response returns (race condition) | Webhook handler looks up by `reference` (idempotency key). Finds `bank_transaction`, updates status. Subsequent initiation response finds existing record via idempotency check and returns it. | 200 to Brankas |
| Brankas webhook arrives twice for same `transaction_id` | Second call finds `bank_transaction` already `SETTLED`. No-op. Return 200. | 200 to Brankas |
| Brankas signature validation fails | Return 401. Log attempted call with IP. | 401 |
| Admin retries after Brankas 5xx, but ledger entry was actually written (partial failure) | Idempotency-Key check finds existing `ledger_entry`. Returns it. No duplicate. | 202 with existing record |
| Disbursement attempted on contract with wrong status | Return 400 with `"Contract must be ACTIVE_FUNDED"` | 400 |

---

## 8. Acceptance Criteria

- [ ] `test_disbursement_happy_path` — given ACTIVE_FUNDED contract, POST returns 202, ledger_entry created with type=DISBURSEMENT, bank_transaction created with status=PENDING
- [ ] `test_disbursement_idempotency` — given same Idempotency-Key, second POST returns 202 with existing record, no duplicate ledger_entry or bank_transaction
- [ ] `test_disbursement_requires_admin_role` — given SME or INVESTOR JWT, returns 403
- [ ] `test_disbursement_requires_active_funded_contract` — given contract in ACTIVE_PENDING_FUNDING, returns 400
- [ ] `test_disbursement_requires_funded_listing` — given listing not yet FUNDED, returns 400
- [ ] `test_disbursement_brankas_failure_no_ledger_write` — given mocked Brankas 500, no ledger_entry or bank_transaction written, returns 502
- [ ] `test_disbursement_insufficient_omnibus_balance` — given mocked Brankas balance below amount, returns 400
- [ ] `test_webhook_settled` — given valid Brankas `payment.settled` webhook, bank_transaction updated to SETTLED, audit_log written
- [ ] `test_webhook_failed` — given valid Brankas `payment.failed` webhook, bank_transaction updated to FAILED, failure_reason set
- [ ] `test_webhook_idempotency` — given same `payment.settled` webhook twice, second call is no-op, no duplicate writes
- [ ] `test_webhook_invalid_signature` — given wrong HMAC signature, returns 401, no DB writes
- [ ] `test_webhook_race_condition` — given webhook arriving before initiation response, bank_transaction updated correctly on subsequent initiation response

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Which Brankas product handles VND outbound bank transfer — PayOut or FundTransfer? | Edward | Pending Brankas integration call |
| 2 | Does Brankas support synchronous balance check or only async polling? | Edward | Pending Brankas API docs review |
| 3 | Ops alert channel for FAILED payments — email, Slack, or both? | Edward | TBD — out of scope for Phase 1 |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | June 2026 | Edward | Initial draft |
