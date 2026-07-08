# Spec: Mock Bank/E-Wallet Account Linking

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/banking/` |
| **Version** | 1.2 |
| **Date** | 2026-07-07 |
| **Related ADR** | ADR-002 (Omnibus/custodial account) — see Open Questions, this spec's existence changes ADR-002's assumptions |
| **Depends on** | None |

---

## 1. Context & Goal

To exercise the full lender (and eventually borrower) flow end-to-end in the UI — "connect a bank/e-wallet account, then fund a project" — the platform needs an account-linking step to call. Brankas integration is not going to happen (per 2026-07-07 decision); no replacement custodial/Open API partner is signed yet, and none is imminent. Rather than block the UI flow on that decision, this spec introduces a permanent mock linking module that stands in for whatever partner is eventually signed.

**Goal:** Give the frontend a real endpoint to call for "connect account" that persists a linked-account record per user, with no real bank/e-wallet connectivity behind it.

---

## 2. Out of Scope

- Any real bank/e-wallet API integration (Brankas or otherwise) — this module is mock-only until a partner is signed, at which point it is replaced, not extended.
- ~~Actually wiring "investor must have a linked account before funding" into `POST /market/listings/{id}/orders`~~ — implemented, see section 10. `app/market/service.py` is normally Phat-owned per `CLAUDE.md` Module Ownership; this one change was made directly by Edward with explicit authorization rather than handed off.
- Enforcing a linked payout account before `POST /payments/disbursements` — same reasoning; `app/payments/` is an existing unspec'd shim, not this spec's concern.
- KYC/KYB identity verification — already live via `app/verification/` (Didit).
- Multiple accounts marked "default," account verification (micro-deposits, etc.), or any notion of account balance.

---

## 3. Data Model

### New Table: `linked_accounts`

```
linked_accounts
├── id                  UUID          PK, default gen_random_uuid()
├── user_id             UUID          NOT NULL → references users(id) ON DELETE CASCADE
├── account_type        TEXT          NOT NULL, CHECK IN ('BANK', 'EWALLET')
├── provider            TEXT          NOT NULL  -- free-text display label, e.g. "Vietcombank", "MoMo"; 'MOCK' if caller omits one
├── account_ref_masked  TEXT          NOT NULL  -- last 4 chars only, e.g. "**** 1234"; the raw account number is never persisted
├── display_name        TEXT          nullable  -- optional user-facing label, e.g. "My salary account"
├── status              TEXT          NOT NULL DEFAULT 'ACTIVE', CHECK IN ('ACTIVE', 'REVOKED')
├── created_at          TIMESTAMPTZ   DEFAULT NOW()
└── updated_at          TIMESTAMPTZ   DEFAULT NOW()
```

No uniqueness constraint — a user may link multiple mock accounts. Only masked digits are stored: the raw `account_number` in the request is used once to derive `account_ref_masked` and is never written to the database, matching how a real tokenized integration (Brankas or otherwise) would behave, so callers don't need to change shape when the real integration replaces this module.

### Alembic Migration

Generated via `alembic revision --autogenerate`, chained off the current head (`862160bce972`).

---

## 4. API Contract

### `POST /banking/accounts/link`

**Auth:** Bearer JWT — roles: `SME` | `INVESTOR`

**Request**
```json
{
  "account_type": "BANK",
  "account_number": "0123456789",
  "provider": "Vietcombank",
  "display_name": "My salary account"
}
```
- `account_type`: required, `"BANK"` or `"EWALLET"`.
- `account_number`: required, non-empty string. Used only to derive the masked reference; never stored raw.
- `provider`: optional, defaults to `"MOCK"`.
- `display_name`: optional.

**Response 201**
```json
{
  "id": "uuid",
  "account_type": "BANK",
  "provider": "Vietcombank",
  "account_ref_masked": "**** 6789",
  "display_name": "My salary account",
  "status": "ACTIVE",
  "created_at": "2026-07-07T00:00:00Z"
}
```

**Error Responses**

| Status | Condition |
|---|---|
| 400 | `account_type` not one of `BANK`/`EWALLET` |
| 400 | `account_number` empty or whitespace-only |
| 403 | caller is not `SME` or `INVESTOR` |
| 422 | Pydantic validation failure |

---

### `GET /banking/accounts`

**Auth:** Bearer JWT — roles: `SME` | `INVESTOR`

Returns the current user's own linked accounts, newest first. No pagination (mock; account counts per user are small).

**Response 200**
```json
[
  {
    "id": "uuid",
    "account_type": "BANK",
    "provider": "Vietcombank",
    "account_ref_masked": "**** 6789",
    "display_name": "My salary account",
    "status": "ACTIVE",
    "created_at": "2026-07-07T00:00:00Z"
  }
]
```

---

### `POST /banking/accounts/{account_id}/unlink`

**Auth:** Bearer JWT — roles: `SME` | `INVESTOR`

Sets `status = REVOKED`. Idempotent: unlinking an already-revoked account returns 200 with the existing record rather than erroring.

**Response 200** — same shape as link response, with `status: "REVOKED"`.

**Error Responses**

| Status | Condition |
|---|---|
| 404 | account does not exist, or does not belong to the calling user |

---

## 5. State Machine

```
ACTIVE  ──[unlink, by owning user]──►  REVOKED
```

`REVOKED` is terminal — there is no re-link; the user links a new account instead. No transition out of `REVOKED`.

---

## 6. Business Rules

1. A user may only link/unlink/list their own accounts — `user_id` is always taken from the JWT, never from the request body.
2. The raw `account_number` is never persisted — only a masked last-4 reference, computed at write time.
3. Linking always succeeds synchronously (mock — no external call, no pending state).
4. Unlinking an already-`REVOKED` account is a no-op success, not an error (matches idempotent-write conventions used elsewhere, e.g. `app/payments/`).

---

## 7. Error Cases

| Scenario | System behaviour | Response |
|---|---|---|
| `account_number` is `""` or all whitespace | Rejected before any DB write | 400 |
| `account_type` is an unsupported value (e.g. `"CRYPTO"`) | Rejected before any DB write | 400 |
| Unlink targets another user's account | Treated as not-found (no existence leak) | 404 |
| Unlink targets an already-revoked account | Returns existing record unchanged | 200 |

---

## 8. Acceptance Criteria

- [x] `test_link_account_happy_path` — given valid input, returns 201 with masked reference, raw account number not present anywhere in the response
- [x] `test_link_account_rejects_blank_account_number` — returns 400
- [x] `test_link_account_rejects_invalid_account_type` — returns 400
- [x] `test_list_accounts_returns_only_callers_own` — a second user's linked accounts never appear
- [x] `test_unlink_account_sets_revoked` — status transitions to REVOKED
- [x] `test_unlink_is_idempotent` — unlinking twice returns 200 both times, no error
- [x] `test_unlink_other_users_account_returns_404` — no cross-user access
- [x] `test_banking_endpoints_reject_admin_role` — ADMIN gets 403 (not a funding party)

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | ADR-002 is titled "Omnibus/custodial account via Brankas" and status ACCEPTED, but Brankas is now not expected to happen. Does ADR-002 get superseded/amended, or does a new ADR record the pivot to "partner TBD, mocked indefinitely"? | Edward | Open — flagged, not resolved by this spec |
| 2 | When a real partner is signed, does `linked_accounts` get replaced outright, or does it become the local cache in front of the partner's own tokenized-account API? | Edward | Deferred to that integration's own spec |
| 3 | Should `POST /market/listings/{id}/orders` require an ACTIVE linked account before accepting funding? | Edward + Phat | **Resolved and implemented (Edward, 2026-07-08): yes, gated at order-attempt time**, not earlier in the funnel (e.g. not right after KYC) — see section 10. Phat should still review, since `app/market/service.py` is normally his file. |

---

## 10. Market Order Precondition (implemented 2026-07-08)

Resolves Open Question #3. Implemented directly by Edward in `app/market/service.py` (cross-owner change, explicitly authorized — normally this file is Phat's) rather than handed off, since the contract below was already fully specified and there was no reason to wait.

**Where:** `app/market/service.py::place_order`, called from `POST /market/listings/{id}/orders`.

**Why gate at order-attempt time, not earlier:** requiring a linked account right after KYC would add friction for users still browsing listings who haven't decided to fund anything yet. Checking it when they submit an order matches the moment they've actually signaled intent to pay, so the "link an account" prompt reads as the natural next step rather than an arbitrary gate.

**What to add:** before creating the `Order` row (recommended: immediately after confirming `Listing.status == "OPEN"`, before the min-ticket/remaining-capacity checks — a missing payment method is a "you can't do this at all" precondition, distinct from "the amount you chose is wrong," so it should surface first), check that the calling investor has at least one `LinkedAccount` with `status == "ACTIVE"`.

**New helper to import:** `app/banking/service.py` will expose:
```python
async def has_active_linked_account(db: AsyncSession, *, user_id: UUID) -> bool
```
This is a small, additive change to `app/banking/` (Edward's module) — Phat does not need to touch `app/banking/` to use it.

**Error contract on failure:**
- Status: `400`
- Body: `{"detail": "No active linked account. Link a bank/e-wallet account before funding."}`
- Matches the existing codebase convention (`CLAUDE.md` Key Conventions → API → Errors: always `{"detail": "<message>"}`, no separate machine-readable error code field). The frontend should match on this exact string to distinguish it from other 400s (min-ticket, capacity) and route to the account-linking prompt rather than a generic error toast.

**Acceptance criteria for the `app/market/` side:**
- [x] `test_place_order_requires_active_linked_account` — investor with no linked account gets 400 with the exact detail string above, no `Order` row created
- [x] `test_place_order_rejects_revoked_only_accounts` — investor whose only linked account is `REVOKED` is treated the same as having none
- [x] `test_place_order_succeeds_with_active_linked_account` — unchanged happy path once an `ACTIVE` account exists

(`tests/lending/test_order_requires_linked_account.py`. The shared `place_order` test fixture in root `conftest.py` now links a mock account by default so every pre-existing order-placement test keeps passing unchanged; pass `link_account=False` to exercise the precondition itself.)

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-07 | Edward | Initial draft — mock linking module replacing the Brankas-specific plan |
| 1.1 | 2026-07-07 | Edward | Resolved Open Question #3; added section 10 (market order precondition contract) for Phat to implement |
| 1.2 | 2026-07-08 | Edward | Implemented section 10 directly in `app/market/service.py` (cross-owner, explicitly authorized) instead of waiting on Phat; marked acceptance criteria done |
