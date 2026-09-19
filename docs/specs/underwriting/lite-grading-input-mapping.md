# Lite Grading — Input Mapping (as implemented)

| Field | Value |
| --- | --- |
| **Status** | IMPLEMENTED — describes code in `main`, not a proposal |
| **Owner** | Phat |
| **Module** | `app/loans/lite_grading.py`, `app/loans/service.py` |
| **Version** | 1.0 |
| **Date** | 2026-09-15 |
| **Describes** | `build_grading_input()` — how typed user input becomes a `GradingInput` |
| **Related** | `grading-engine-core.md` (ACCEPTED) defines `GradingInput`. `grading-input-sources.md` §3.1 is the *inventory of possible* sources and is now **stale in three rows** — see §5. |

> **This is the interim mapping.** No uploaded document is parsed anywhere in the
> codebase, so every engine input either comes from something a person typed, is
> modelled from one, is assumed, or is absent. This document exists so the faked
> parts are visible rather than implied.

---

## 1. Where the user types

Two forms feed the engine. Neither is the document uploads.

| Form | Route | Supplies |
| --- | --- | --- |
| **Project application** | `/project-application` → `POST /projects` | Company identity, industry, headcount, incorporation date, loan amount, term |
| **Loan wizard, steps 2–3** | `/dashboard` wizard → `PUT /loans/applications/{id}/figures` | 10 revenue and cost figures (`LITE_FIGURE_FIELDS`) |

Steps 1, 4 and 5 of the wizard collect documents (charter, registration, e-invoice
archive, CIC report). **None of them reaches the engine.** They are stored for
human verification only.

---

## 2. The mapping — all 22 `GradingInput` fields

Fidelity legend: **typed** = a person entered it · **derived** = computed from a
typed value · **modelled** = invented to a shape from a typed value ·
**assumed** = hardcoded · **table** = platform reference data · **absent** = `None`

| # | `GradingInput` field | Fidelity | Source |
| --- | --- | --- | --- |
| 1 | `company_code` | typed | `projects.tax_id`, falling back to the project UUID. A label only — no grading module reads it |
| 2 | `industry` | typed | `projects.industry`, validated against `supported_industries ∪ excluded_industries` at create time |
| 3 | `company_size` | derived | `company_size_for_headcount(projects.employee_count)` — server-side, never trusted from the client |
| 4 | `loan_size_vnd` | typed | `loan_applications.requested_amount` |
| 5 | `duration_months` | typed | `loan_applications.duration_months` |
| 6 | `operating_months` | derived | Calendar months from `projects.incorporation_date` to today (`_operating_months`) |
| 7 | `monthly_revenue` | **modelled** | 24 values built from 2 annual totals — see §3 |
| 8 | `cogs_y1` | typed | `cogs_y1` (step 3) |
| 9 | `fixed_cost_y1` | typed | `fixed_cost_y1` (step 3) |
| 10 | `variable_cost_excl_cogs_y1` | typed | `variable_cost_excl_cogs_y1` (step 3) |
| 11 | `conc_top1_pct` | typed | `conc_top1_pct` (step 3, optional) |
| 12 | `conc_top3_pct` | typed | `conc_top3_pct` (step 3, optional) |
| 13 | `crr` | **absent** | `None` — customer retention, not collected |
| 14 | `rri` | **absent** | `None` — revenue-retention index, no definition |
| 15 | `tcp` | **absent** | `None` — no source identified |
| 16 | `sector_cagr_pct` | table | `sector_reference_v1.yaml` → `cagr_pct` for the industry |
| 17 | `ai_scores` | table + **absent** | 6 of 7 from the sector table; `founder` is omitted — see §4 |
| 18 | `owner_withdrawal` | typed | `owner_withdrawal_pct` (step 3, optional) |
| 19 | `cic_score` | **modelled** | Not collected. Bracketed 442–750 — see §3 |
| 20 | `kyc_aml_passed` | **assumed** | Hardcoded `True` — see §4 |
| 21 | `fraud_flags` | **assumed** | Hardcoded `()` |
| 22 | `bank_rate_pct` | default | Dataclass default `12.0`; never asked of the user |

**Tally, 22 fields:** 12 typed or derived · 2 modelled · 3 assumed/default ·
3 absent · 2 from the reference table (one of which, `ai_scores`, is itself
6-of-7 complete).

So **roughly half** of what the engine scores is something a person actually
stated. The rest is modelled, assumed, table-sourced or missing — which is the
honest reason the output is an indicative band and not a quote.

### The 10 typed figures, in wizard order

| Wizard field | Engine field | Required |
| --- | --- | --- |
| Tổng doanh thu 12 tháng gần nhất | `monthly_revenue` m13–m24 (magnitude) | ✅ |
| Tổng doanh thu 12 tháng trước đó | `monthly_revenue` m1–m12 (magnitude) | ✅ |
| Doanh thu tháng cao nhất | `monthly_revenue` m13–m24 (shape) | — |
| Doanh thu tháng thấp nhất | `monthly_revenue` m13–m24 (shape) | — |
| Giá vốn hàng bán | `cogs_y1` | ✅ |
| Chi phí cố định | `fixed_cost_y1` | ✅ |
| Chi phí biến đổi | `variable_cost_excl_cogs_y1` | ✅ |
| Chủ sở hữu rút vốn % | `owner_withdrawal` | — |
| Tập trung khách hàng top 1 % | `conc_top1_pct` | — |
| Tập trung khách hàng top 3 % | `conc_top3_pct` | — |

---

## 3. The two modelled inputs

**`monthly_revenue` (24 values from 2 numbers).** The engine refuses to score a
short series or any `None`, and no applicant will type 24 figures. So the annual
total sets the **magnitude** and the optional best/worst month set the **shape**:
a triangular seasonal curve, floored at a 2% worst-to-best ratio, rescaled to hit
the stated total exactly. `m1..m12` is the **earlier** year — reversing this
inverts every growth and trend derivation.

This matters because the engine scores revenue *stability*. **With best/worst
left blank the curve is flat, which reads as a perfectly steady business and
flatters the applicant.** That case is disclosed in the returned `assumptions`.

**`cic_score` (a range, not a value).** The CIC report is the only possible
source and is unparsed, and the Lite flow deliberately does not ask for the
number — CIC is the sensitive document SMEs will not hand over pre-signup. So the
engine runs **twice**, at 442 and 750 (the range the golden set actually covers),
and the two rates bracket the answer.

**This is the entire reason the result is a band rather than a rate.** Parse the
CIC report and the band collapses to a single grade.

---

## 4. What is assumed, and why it is safe *only* pre-offer

| Assumption | Value | Why | Risk if it leaks into an offer |
| --- | --- | --- | --- |
| `kyc_aml_passed` | `True` | Gate 6 is a hard REJECT on `False`; a pre-KYC estimate must assume a pass or every band reads REJECT | An applicant who fails KYC was shown a rate they can never have |
| `fraud_flags` | `()` | Same gate, same reason | As above |
| `founder` AI score | omitted | Company-specific; the sector table cannot supply it. The engine reports `AI_PENDING` and still prices — by design (R3/R8) | One of seven AI factors never contributes |
| Sector table | `DRAFT_UNREVIEWED` | `reviewed_by: null`; **sector drives 36% of the spread** | Every band is provisional until the CEO signs it off |

All four are surfaced to the applicant in `LiteBand.assumptions`, and
`provisional` is `True` while the sector table is unreviewed. **The UI is
required to render both.**

---

## 5. Corrections to `grading-input-sources.md` §3.1

Three rows are now out of date. The columns exist as of migration
`a4e91c2d7b58`:

| # | Field | §3.1 says | Actually |
| --- | --- | --- | --- |
| 3 | `company_size` | ⚠️ "`projects` has no column, so it is dropped" | ✅ Persisted, derived server-side |
| 5 | `duration_months` | ⚠️ "`loan_applications` has no column, so it is dropped" | ✅ Persisted |
| 6 | `operating_months` | ⚠️ "derivation not implemented anywhere yet" | ✅ `_operating_months()` |

Rows 9/10 (`fixed_cost_y1`, `variable_cost_excl_cogs_y1`) are marked ❌ "not
stated by any statutory document" — still true of documents, but both are now
**typed directly**, which is why the Lite flow exists.

§3.1 is Edward's to amend; this table records the divergence rather than editing
his spec.

---

## 6. Closing the gaps, by value

1. **Parse the CIC report** → replaces the 442–750 bracket with a real
   `cic_score`. Collapses the band to one grade. Highest value by far, and the
   document is already collected at wizard step 5.
2. **Parse the e-invoice archive** → replaces the modelled `monthly_revenue`
   with 24 real months, and could supply `conc_top1/top3` and `crr` from the
   buyer ledger. Also where Handbook §5.10's signature and
   invoice-continuity checks belong.
3. **Review the sector table** → clears `provisional` on every band.
4. **Source the `founder` AI score** → completes `ai_scores`.
5. `rri` and `tcp` have no definition, and factor 12 needs **all three** of
   `crr`/`rri`/`tcp` — one missing zeroes the bonus, so `crr` alone gains
   nothing.

---

## 7. Verifying this document

`tests/loans/test_lite_grading.py` covers the adapter (series length, year
order, shape); `tests/loans/test_indicative_rate.py` covers the wiring end to
end, including that a worse cost base prices worse — the check that the typed
figures actually reach the engine rather than a default being scored.
