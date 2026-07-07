# Spec: Mock Bank/E-Wallet Account Linking

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/banking/` |
| **Version** | 1.0 |
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
- Enforcing "investor must have a linked account before funding" inside `POST /market/listings/{id}/orders` — that endpoint lives in `app/market/` (Phat-owned per `CLAUDE.md` Module Ownership). Wiring the check in is a follow-up that needs Phat's agreement before either side edits `app/market/service.py`.
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
| 3 | Should `POST /market/listings/{id}/orders` require an ACTIVE linked account before accepting funding? | Edward + Phat | Deferred — needs joint agreement since it touches Phat-owned `app/market/` |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-07 | Edward | Initial draft — mock linking module replacing the Brankas-specific plan |
