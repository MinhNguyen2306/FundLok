# Spec: Grading Engine — Input Sources & Field Mapping

| Field | Value |
|---|---|
| **Status** | DRAFT |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend ingest + admin entry API) / Phat (application form, admin entry UI) |
| **Module** | `app/underwriting/`, `app/projects/`, `app/loans/`, `app/uploads/` |
| **Version** | 0.1 |
| **Date** | 2026-08-24 |
| **Related ADR** | — |
| **Depends on** | `grading-engine-core.md` (ACCEPTED v1.0) — defines `GradingInput`. `grading-engine-integration.md` (DRAFT) — this doc is the input inventory that spec needs before it can be written. |

---

## 1. Context & Goal

The grading core is finished and reconciles against all 10,000 golden-set rows, but nothing feeds it:
`app/underwriting/service.py::start_score_run` still returns the hardcoded mock. Before the wiring
spec can be written, someone has to answer a plainer question — **for each of the ~24 fields
`GradingInput` requires, where does the value actually come from, and do we collect it today?**

This document is that inventory. It is deliberately not an implementation plan: it records the
mapping, names the fields nothing supplies, and lists the decisions those gaps need. Three of the
gaps are not "wire up a parser" problems — they need a business decision from Loc first.

**Goal:** a per-field mapping from every `GradingInput` field to a concrete source, with each gap
either closed or written down as an owned open question.

---

## 2. Out of Scope

- All calculation. Owned by `grading-engine-core.md`.
- The document parsers themselves (VAT XML, B02-DN, CIC PDF). This doc says what each parser must
  produce; how it parses is a separate spec.
- The AI scoring service and its rubrics (D26/D27).
- Persisting a score run and routing its outcome. That is `grading-engine-integration.md`.
- KYC/KYB verification mechanics — already specified under `docs/specs/gverify/`. This doc only
  records which `GradingInput` fields those flows supply.

---

## 3. Data Model

### 3.1 Field inventory

Source column: **form** = SME application form · **doc** = uploaded document · **derived** =
computed from another field · **platform** = FL-side config/table · **verify** = KYC/KYB module.

Status: ✅ available today · ⚠️ collected but not usable (unparsed, or dropped before storage) ·
❌ no source.

| # | `GradingInput` field | Type | Source | Status | Notes |
|---|---|---|---|---|---|
| 1 | `company_code` | str | form | ✅ | `legal_name` + `tax_id` on `projects` |
| 2 | `industry` | str | form | ✅ | Must be one of the 15 `supported_industries`. Frontend now submits the engine's exact strings (`lib/constants/industries.ts`) |
| 3 | `company_size` | micro/small/medium | derived | ⚠️ | Derived from `employee_count` via `company_sizes` bands. Form collects it; **`projects` has no column, so it is dropped** |
| 4 | `loan_size_vnd` | Decimal | form | ✅ | `loan_applications.requested_amount`. Engine bounds 200M–5bn |
| 5 | `duration_months` | int (3/6/9/12) | form | ⚠️ | Form collects it; **`loan_applications` has no column, so it is dropped** |
| 6 | `operating_months` | int | derived | ⚠️ | From `projects.incorporation_date`; derivation not implemented anywhere yet |
| 7 | `monthly_revenue` | 24 × Decimal | doc | ⚠️ | VAT declarations and/or e-invoice data. Unparsed. See §6.2 — quarterly filers cannot satisfy this from VAT alone |
| 8 | `cogs_y1` | Decimal | doc | ⚠️ | B02-DN "Giá vốn hàng bán". Unparsed |
| 9 | `fixed_cost_y1` | Decimal | doc + judgment | ❌ | **Not stated by any statutory document.** See §6.1 |
| 10 | `variable_cost_excl_cogs_y1` | Decimal | doc + judgment | ❌ | Same as above |
| 11 | `conc_top1_pct` | float? | doc | ❌ | Needs an invoice-level customer ledger. E-invoice data may contain one — see §9 Q2 |
| 12 | `conc_top3_pct` | float? | doc | ❌ | As above |
| 13 | `crr` | float? | doc | ❌ | Customer retention; derivable from buyer sets across periods if the e-invoice ledger is complete |
| 14 | `rri` | float? | ❌ | ❌ | Revenue-retention index; no source identified |
| 15 | `tcp` | float? | ❌ | ❌ | No source identified. Note factor 12 needs **all three** of `crr`/`rri`/`tcp`; one missing zeroes the bonus |
| 16 | `sector_cagr_pct` | float | platform | ⚠️ | `sector_reference_v1.yaml` `cagr_pct`. Drafted, `reviewed_by: null`, not wired |
| 17 | `ai_scores` (7 keys) | 0–100 each | platform + AI | ❌ | 6 sector factors from the reference table (unreviewed); `founder` has no source at all (D26/D27) |
| 18 | `owner_withdrawal` | float? | doc | ❌ | Not in B02-DN. Would come from B03-DN, the equity note, or bank statements — none collected. See §9 Q3 |
| 19 | `cic_score` | int? | doc | ⚠️ | CIC report upload is the only possible source. Unparsed |
| 20 | `kyc_aml_passed` | bool? | verify | ✅ | GVerify KYB (SME) — `gverify_kyb_verifications.status == APPROVED` |
| 21 | `fraud_flags` | tuple[str] | verify | ✅ | Same source; empty tuple when clean |
| 22 | `bank_rate_pct` | float | platform | ✅ | Config, default 12.0. Never asked of the user |

### 3.2 Upload coverage

The wizard collects six documents. Two of them feed no engine field:

| Upload (`document_type`) | Feeds | Fields |
|---|---|---|
| `legal_charter` | nothing in the engine | — (KYB/legal review only) |
| `business_registration` | indirectly | corroborates #2, #6 |
| `vat_tax_zip` | revenue | #7 |
| `financial_report` (B02-DN) | costs | #8, and the raw material for #9/#10 |
| `e_invoice_data` | revenue at monthly granularity; possibly the customer ledger | #7, potentially #11–#13 |
| `cic_report` | credit score | #19 |

**Not collected, and worth a decision:** balance sheet (B01-DN), cash-flow statement (B03-DN), bank
statements. See §9 Q3 and Q4.

### 3.3 Schema changes needed to stop dropping collected data

The form already collects three engine-required values that the API accepts and discards, because
`app/core/config.py` sets `extra="ignore"`.

```
Modified table: loan_applications
+ duration_months   INTEGER   nullable   -- loan term; engine allowed_durations_months (3/6/9/12)

Modified table: projects
+ employee_count    INTEGER   nullable   -- headcount as entered by the SME
+ company_size      TEXT      nullable   -- CHECK IN ('micro','small','medium'); see §6.3
```

Nullable because existing rows predate the columns. One Alembic migration off the current head
covers all three; revision id assigned at implementation time.

Matching schema fields: `LoanApplicationCreateInline`, `ProjectCreate`, `ProjectOut`,
`ProjectLoanApplicationOut`.

---

## 4. API Contract

No new endpoint is proposed here — this doc's output is the mapping. Two contract changes follow
from §3.3, and one from §6.4.

### `POST /projects` — additive fields

**Request** (additions only)
```json
{
  "employee_count": 25,             // required, integer 1..200
  "company_size": "small",          // OPTIONAL from the client; server derives — see §6.3
  "loan_application": {
    "duration_months": 9            // required when loan_application is present; one of 3,6,9,12
  }
}
```

**Error Responses**

| Status | Code | Condition |
|---|---|---|
| 422 | — | `employee_count` outside 1–200 |
| 422 | — | `duration_months` not in {3, 6, 9, 12} |
| 400 | `INDUSTRY_NOT_SUPPORTED` | `industry` not in `supported_industries` ∪ `excluded_industries` |

### `GET /underwriting/industries` — new, proposed (§6.4)

**Auth:** Bearer JWT — any authenticated role.

**Response 200**
```json
{
  "industries": ["Retail Trade", "IT Services", "..."],
  "params_version": "wb-v0-20260728"
}
```

Exists so the frontend dropdown cannot drift from `grading_params_v1.yaml`. Today
`lib/constants/industries.ts` mirrors the YAML by hand, which is a known drift risk — 7 of the 9
pre-existing options were values the engine rejected outright.

---

## 5. State Machine

No new status field. One consequence for an existing one, carried over from
`grading-engine-integration.md` §Open Questions: `ScoreRun.status` is `RUNNING → READY → LOCKED`
and has nowhere to put `INSUFFICIENT_DATA` or `AI_PENDING`. Until that enum is extended (a shared
model change needing both engineers' agreement), an application missing any field above cannot be
represented as a score run at all.

---

## 6. Business Rules

### 6.1 The fixed/variable cost split needs a stated policy

The engine takes `cogs_y1`, `fixed_cost_y1` and `variable_cost_excl_cogs_y1` as three separate
figures. Form B02-DN reports cost of goods sold, selling expenses and administrative expenses.
Selling and admin expenses each contain both fixed and variable components; no statutory statement
splits them.

This is not a rounding detail. `contribution_margin` and `cost_flexibility` are weighted 0.20 each
within BCQ, and BCQ is 0.40 of the final grade — so **~16% of the grade** depends on a
classification no document states. Two SMEs with identical B02-DNs can score differently depending
on who classified their costs.

Until a policy exists, the value is an admin-entered judgement and must be recorded as such
(who entered it, when) so a decision can be defended. Options for the policy: a fixed per-industry
ratio in the sector table; a standard mapping of B02-DN lines to fixed/variable; or an explicit
underwriter classification step with the reasoning stored.

### 6.2 24 months of revenue, and what quarterly VAT filers can supply

`_is_insufficient_data()` requires exactly 24 non-null monthly figures. `revenue_volatility_cv`,
`revenue_trend_decimal` and `seasonality_ratio` — 3 of the 22 factors, and the whole of the RSG
core — are computed from them.

Vietnamese SMEs under the revenue threshold file VAT **quarterly**: 8 data points over two years,
not 24. For those borrowers the VAT zip alone cannot satisfy the engine, and no interpolation is
acceptable — spreading a quarter evenly across three months fabricates exactly the volatility and
seasonality signal those three factors measure.

**Rule:** e-invoice data is the primary source for `monthly_revenue`; VAT declarations are the
cross-check. For a quarterly filer without e-invoice data the honest outcome is
`INSUFFICIENT_DATA`, not a grade. The wizard should say so at the E-Invoice step, since a borrower
who skips it is not losing detail — they are unscoreable.

### 6.3 Derivations

| Target | Rule |
|---|---|
| `company_size` | Band containing `employee_count` per `company_sizes` (micro 1–10, small 11–50, medium 51–200). Headcount > 200 has no band — reject at the form; it is outside the SME ceiling this product underwrites |
| `operating_months` | Whole months between `projects.incorporation_date` and the score-run date. Under 24 fires soft gate 1 (REVIEW), so the form should warn before submit |
| `revenue_y1` | `sum(m13..m24)` — the engine's own derivation; ingest must preserve month ordering, `m1` oldest |

`company_size` should be derived **server-side** from `employee_count`, not trusted from the
client: the bands live in the params file, so the mapping belongs next to it. The client may send
its own derived value for display purposes, but the server recomputes.

### 6.4 Vocabulary ownership

`grading_params_v1.yaml` is the source of truth for `supported_industries`, `company_sizes` and
`loan_constraints`. The frontend currently mirrors all three by hand
(`lib/constants/industries.ts`, `company-size.ts`, `loan-constraints.ts`), each with a TODO
pointing here. §4's endpoint removes the industry mirror; the numeric constraints are stable enough
that mirroring them is acceptable for now.

---

## 7. Error Cases

What the engine does when a field is absent, so ingest knows what it must guarantee versus what it
may pass through as null.

| Condition | Engine behaviour | Ingest must |
|---|---|---|
| `industry` in neither supported nor excluded list | `ValueError` | Validate before calling `grade()` |
| `loan_size_vnd` outside 200M–5bn | `ValueError` | Validate at the form and again server-side |
| `duration_months` not in {3,6,9,12} | `ValueError` | As above |
| `bank_rate_pct >= rate_cap_pct` | `ValueError` | Config error; never user-driven |
| Fewer than 24 months, or any month null | returns `INSUFFICIENT_DATA` | Surface which document is missing — the engine does not say |
| `cic_score` or `kyc_aml_passed` null | returns `INSUFFICIENT_DATA` | As above |
| `revenue_y1`, `total_cost` or `min(m13..m24)` is 0 | returns `INSUFFICIENT_DATA` | As above |
| `profit <= 0` | **raises `ValueError`** | Catch it. A loss-making applicant is a legitimate submission, not a 500 |
| Any of the 7 `ai_scores` missing | returns `AI_PENDING`, deterministic premiums still computed | Persist the partial result; do not price off it |
| `conc_*`, `crr`/`rri`/`tcp`, `owner_withdrawal` null | bonus contributes 0, no penalty | Pass null through; do not substitute 0 |

The distinction matters: `INSUFFICIENT_DATA` is a return value to store and show, while `ValueError`
is a bug or a validation miss and must never reach the user as a 500.

---

## 8. Acceptance Criteria

1. `test_industry_endpoint_returns_engine_supported_list` — `GET /underwriting/industries` returns
   exactly `supported_industries` from the loaded `ParamSet`.
2. `test_create_project_persists_employee_count_and_company_size` — round-trips through
   `POST /projects` → `GET /projects`.
3. `test_company_size_is_derived_server_side_not_trusted` — a client-sent `company_size` that
   contradicts `employee_count` is overwritten by the derived band.
4. `test_employee_count_above_two_hundred_rejected` — 201 employees → 422.
5. `test_create_loan_application_persists_duration_months` — round-trips; a value outside
   {3,6,9,12} → 422.
6. `test_operating_months_derived_from_incorporation_date` — a company incorporated 18 months ago
   yields `operating_months == 18` and fires soft gate 1.
7. `test_quarterly_vat_only_applicant_is_insufficient_data` — 8 quarterly figures produce
   `INSUFFICIENT_DATA`, never an interpolated 24-month series.
8. `test_loss_making_applicant_does_not_500` — `profit <= 0` surfaces as a handled state.
9. `test_missing_ai_scores_yield_ai_pending_with_deterministic_premiums` — bcq/rsg/behavioral are
   present and non-null.

---

## 9. Open Questions

| # | Question | Owner | Blocking |
|---|---|---|---|
| Q1 | **Fixed/variable cost policy** (§6.1). Per-industry ratio, a standard B02-DN line mapping, or an underwriter judgement call with stored reasoning? ~16% of the grade depends on the answer | Loc / Edward | Any real grade |
| Q2 | **Does `e_invoice_data` contain the full invoice-level ledger** (buyer name + tax code per invoice)? If yes, `conc_top1`, `conc_top3` and `crr` become computable and D25's premise ("no source provides one") should be revisited — that is 3 bonus factors currently scoring 0 for every applicant | Edward | No — improves grades |
| Q3 | **`owner_withdrawal` source.** Add B03-DN or bank statements to the wizard, or accept the factor as permanently absent? | Loc | No — bonus factor |
| Q4 | **No leverage factor.** None of the 22 factors reads the balance sheet, so total existing debt never enters the grade; CIC covers repayment history only. An applicant with three other active loans scores the same as one with none. Intentional, or a missing factor plus a missing B01-DN upload? | Loc | No — model question |
| Q5 | **`rri` and `tcp` have no identified source at all** (#14, #15). Since factor 12 needs all three of `crr`/`rri`/`tcp`, the RTI bonus is unreachable until they do. Define them or drop the factor? | Loc | No — bonus factor |
| Q6 | **Construction & Real Estate.** The engine's 15 industries include `Construction Materials` but no real-estate sector, so a property developer has no honest option in the dropdown. Add a sector row, or is this out of appetite? | Loc | Blocks those applicants |
| Q7 | **Where does admin financial entry live?** Until parsers exist, someone types 24 revenue figures and 3 cost figures per application. Which module owns that screen and API — `app/admin/` (Phat) or a new underwriting-side entry endpoint (Edward)? | Both | Yes — first real score run |
