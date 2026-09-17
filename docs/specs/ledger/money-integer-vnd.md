# Spec: Money to Integer VND

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/lending/`, `app/ledger/`, `app/payments/` |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | ADR-003 (omnibus-first ledger) |
| **Depends on** | `docs/specs/ledger/ledger-foundation.md` |

---

## 1. Context & Goal

The Vietnamese đồng (VND) has no circulating sub-unit — the smallest real
unit of currency is 1 VND. The repayment mechanism spec (§14, "FundLok Fixed
Daily Repayment Mechanism Spec v1.3") states: *"Money is integer VND
everywhere. No sub-unit. No decimals anywhere in the system."* Every money
column in the codebase was instead `Numeric(15,2)` / `Numeric(12,2)` —
hundredths of a đồng, a unit that does not exist. HANDOFF-03 Issue 7: INV-1
(`collected + outstanding = total`, exactly, at all times) is trivially
assertable over integers and permanently fragile over a 2-dp scale.

**Goal:** every money-denominated column, DTO field and calculation in the
codebase operates on whole VND, with no floats and no fractional decimals,
before the facility/repayment tables (T6+) are built on top of it.

---

## 2. Out of Scope

- `score_runs.overall_score` (`Numeric(5,2)`) — a grade score, not money.
  Covered separately by HANDOFF-03 Issue 4 / T4.
- `holdings.share_ratio` (`Numeric(10,8)`) — a proportion, not money.
- Any new facility/schedule/payment tables — those are built integer-native
  from the start under T6/T7, and are not part of this migration.

---

## 3. Data Model

### Modified columns

```
ledger_entries.amount                Numeric(15,2) -> Numeric(20,0)
contracts.target_amount              Numeric(15,2) -> Numeric(20,0)
contracts.funded_amount              Numeric(15,2) -> Numeric(20,0)
listings.target_amount               Numeric(15,2) -> Numeric(20,0)
listings.funded_amount               Numeric(15,2) -> Numeric(20,0)
listings.min_ticket                  Numeric(12,2) -> Numeric(20,0)
orders.amount                        Numeric(15,2) -> Numeric(20,0)
holdings.principal                   Numeric(15,2) -> Numeric(20,0)
loan_applications.requested_amount   Numeric(15,2) -> Numeric(20,0)
```

`Numeric(20,0)` gives headroom well beyond any realistic VND loan size
(up to 10^20 - 1 đồng) with zero decimal places.

### Alembic Migration

`alembic/versions/ca8a6db6183e_money_to_integer_vnd.py`, chained off
`d5a8c31f6b02` (prior head). Uses `ROUND(<col>)::numeric(20,0)` on upgrade
so any pre-existing fractional value is rounded to the nearest đồng rather
than silently truncated or rejected.

---

## 4. API Contract

No new endpoints. Every existing request/response field listed above
changes Pydantic type from `Decimal` to `int`:

- `LoanApplicationCreate.requested_amount`, `LoanApplicationOut.requested_amount`
- `ContractOut.target_amount`, `ContractOut.funded_amount`
- `ListingCreate.target_amount`, `ListingCreate.min_ticket`,
  `ListingOut.target_amount`, `ListingOut.min_ticket`, `ListingOut.funded_amount`
- `OrderCreate.amount`, `OrderOut.amount`
- `DisbursementCreate.amount`
- `RepaymentCreate.amount`, `DistributionOut.amount`

A request body carrying a fractional value (e.g. `"1000.50"`) is rejected
with a 422 (Pydantic's `int` coercion rejects non-integral input; verified:
an integral-valued numeric string such as `"10000.00"` still coerces
cleanly to `10000`, so no caller needs to change how it formats a whole-VND
amount).

---

## 5. State Machine

Not applicable — no status field is introduced or changed by this spec.

---

## 6. Business Rules

1. No money value anywhere in the system carries a fractional component.
2. Distribution of a repayment across N holdings uses Hamilton's
   largest-remainder apportionment over integer VND (see §7): each
   holding's exact entitlement is `principal * amount // total_principal`
   (floor), and the `amount - sum(floors)` leftover whole đồng are handed
   out one at a time to the holdings with the largest fractional
   remainder, ties broken by holding id for determinism. This always sums
   to exactly `amount`, including `amount` as small as 1 VND.
3. A holding whose final apportioned share is 0 gets no `DISTRIBUTION` leg
   at all — `post_transaction()` rejects zero-amount legs by construction
   (see `docs/specs/ledger/ledger-foundation.md`), and a zero-value leg
   would carry no economic meaning.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Request carries a fractional VND amount (e.g. `"100.50"`) | Pydantic `int` field validation fails | 422 |
| Repayment amount smaller than the number of holdings (e.g. 1 VND, 3 holdings) | Largest-remainder apportionment gives most holdings a 0 share; those are skipped, one holding gets the whole 1 VND | 201, `balances` has fewer entries than there are holdings |
| Pre-existing DB row holds a fractional value at migration time | `ROUND(...)::numeric(20,0)` rounds to the nearest đồng on upgrade | — (migration-time, not a runtime path) |

---

## 8. Acceptance Criteria

- [x] `test_repayment_splits_across_uneven_holdings_without_imbalance` — three holdings whose exact entitlements are non-integer VND still sum to exactly the repaid amount
- [x] `test_repayment_of_one_vnd_across_three_holdings_sums_to_exactly_one` — a repayment of 1 VND split across 3 holdings sums to exactly 1, with zero-value legs skipped
- [x] Existing ledger tests (`tests/ledger/`, `tests/lending/`) pass unmodified except for the two fractional-amount fixtures listed in the changelog
- [x] No `quantize(Decimal("0.01"))` remains under `app/`
- [x] The Alembic migration chains off the current head with a hash revision ID

---

## 9. Open Questions

None.

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial migration to integer VND (T1, HANDOFF-03). Rewrote `tests/lending/test_repayment_distribution_rounding.py` (previously exercised 2dp cent-rounding, now exercises integer largest-remainder apportionment) and fixed one fractional `Decimal("1234.56")` literal in `tests/ledger/test_ledger_foundation.py`. |
