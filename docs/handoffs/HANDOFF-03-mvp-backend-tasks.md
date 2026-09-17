# HANDOFF-03 — MVP Backend Task Breakdown

| Field | Value |
|---|---|
| **Status** | FOR IMPLEMENTATION |
| **Version** | 0.4 — 17 September 2026 |
| **Author** | Edward Wong (CTO) |
| **Implementer** | Sonnet |
| **Target** | Demo-grade MVP, 20 September 2026 |
| **Inputs** | `BackEnd.docx` (Loc), `FundLok_Fixed_Daily_Repayment_Mechanism_Spec_v1_3.docx` (Loc), `FundLok_Sector_Risk_Lookup_v1.xlsx` |
| **Baseline** | `docs/module-completion-audit-2026-08.md` (11 Aug 2026) |

**Changes in v0.5.** Loc confirmed no FundLok fee during MVP. Recorded as S6, with the structural half
decided rather than deferred. T14 is rewritten: the fee *rate* defaults to 0, but the split path is
built now, and at a zero rate the FEE leg is **omitted, not posted as zero** — `post_transaction`
rejects any leg with `amount <= 0`. T19 gains a warning about publishing a net APY on a zero fee.

**Changes in v0.4.** T0e and T0f resolved — see the new §5. Response shapes are specified and are the
contract with Phat. `LENDER` becomes the outstanding claim (so `DISTRIBUTION` debits it); a new
`INVESTOR_CASH` account type holds uncommitted investor cash, and `SUSPENSE` stays reserved for
unattributed funds. Two defects in the existing ledger convention are recorded, and **T21 (funding-flow
spec) is added and now blocks T10 and T14.**

**Changes in v0.3.** Loc answered T0a and T0b. `sector_reference_v1.yaml` is the engine table and the
**frontend industry list changes to its 15 industries** — the xlsx is not adopted anywhere. Gate 3 is
enabled at `threshold: 13`. `bank_rate_pct` becomes a config constant at 12.0 with scheduled review.
T3, T4 and T5 are unblocked. Issue 17 records the industry-enum hazard this creates.

**Changes in v0.2.** Loc confirmed manual disbursement with a matching double-entry posting, and
explained the xlsx re-anchoring as an attempt to keep factor scores off the knockout rules. T0a
rewritten around the gate-3 threshold; T10 and T13 merged into one bank-movement endpoint; two new
blockers on the ledger account model recorded (Issues 15–16); the Issue 2 arithmetic corrected — one
claim in v0.1 was wrong and is withdrawn below.

---

## 0. Scope decisions taken for this handoff

These were open in the brief. They are settled here; change them in this file, not in chat.

| # | Decision | Consequence |
|---|---|---|
| S1 | **One FBO omnibus custodial account.** Not per-project. | Matches ADR-003 and `custodial_accounts.scope='PLATFORM'` exactly as built. Zero migration. The `scope='CONTRACT'` seam stays dormant for a later escrow pivot. |
| S2 | **Bank gives us statement export only.** No pull, no payout API. | All collection is SME-initiated push, detected by reconciling inbound transfers (spec D18). |
| S3 | **Demo target, not a live pilot.** Real logic, no real money. | |
| S4 | **Extensions are out of MVP scope.** | Build spec §4.1, §4.5, §5, §6. Do **not** build §4.2, §4.4, §7. See Issue 8. |
| S5 | **Disbursement is executed manually and mirrored into the ledger.** *(new, v0.2)* | Every real bank movement is recorded through one ops endpoint that posts the matching ledger transaction. Manual entry now, statement import later, **one code path** — see T10. |
| S6 | **No FundLok fee during MVP** (Loc, 17 Sep). The *rate* is deferred; the *structure* is not. *(new, v0.5)* | Fee rate is config, default `0`. **The fee is taken from the investor's return, never added to the borrower's cost** — so `T₀ = P + I` is untouched, INV-5's cap test stays clean, and counsel question C3 does not gate the build. Consistent with D7 ("passes through to investors; FundLok takes its agreed cut"). See T14. |

---

## 1. Is `BackEnd.docx` consistent with the goal?

Yes, with one correction and one omission.

**It is consistent.** Moving SME pricing server-side is right, and for the reason Loc gives: the formula
is a trade secret and the numbers have to be real. Capturing the investor lead *before* the yield is
revealed, and keying the sign-up update on email rather than writing a second record, are both correct.
Showing the number when lead capture fails is the right call — it is our outage, not the user's.

**The correction.** Loc's note says the investor calculator "can be client side… but move the
calculation out of the bundle. Or lock it somewhere." There is no way to put JavaScript in a browser
and not have it be readable. Moving it to a separate file or minifying it is obfuscation, not
protection, and the investor maths embeds the expected-loss constant. It is four fields in and five
numbers out — make it an endpoint and it costs nothing.

**The omission.** `BackEnd.docx` specifies four endpoints, all on the public landing page. It is a
marketing-site spec. It contains nothing about matching, funding, disbursement, the ledger or
repayment — which is the actual MVP. Read it as one workstream (T15–T17), not as the backend plan.

---

## 2. Blocking and near-blocking issues

### 2.1 Underwriting and pricing

**Issue 1 — The grading engine cannot score a single real application today.**
`GradingInput.ai_scores` requires seven keys (`regulatory`, `input_cost_vol`, `cyclicality`,
`competitor`, `macro`, `uncontrollable`, `founder`). Nothing populates them, so `grade()` returns
`AI_PENDING` for every input. `sector_reference_v1.yaml` holds 105 values that would supply six of the
seven, but **no loader exists** and the file is headed *"CRITICAL — DO NOT WIRE THIS INTO grade()"*.
The August audit confirmed this by direct call. This is the single thing standing between a finished,
10,000-row-verified engine and a working product.

**Issue 2 — The uploaded xlsx and the in-repo sector table are different tables.**

*Withdrawn from v0.1:* the concern that the xlsx's "Sector Premium = simple average of the 7" might
disagree with the engine was **wrong**. `rollup.sector.core` weights all seven columns at exactly 1/7.
Loc's method matches the engine precisely.

*Corrected magnitude.* `final_grade` weights are `bcq 0.40 / rsg 0.25 / sector 0.25 / behavioral 0.10`,
and the rate moves 8pp across the grade range at `bank_rate = 12`. So **one sector premium point is
worth exactly 2bp on the rate**. (Validated against the yaml's own `differentiation` note: its
38.89–71.97 range × 0.25 × 8pp = 66bp, which is the figure the file claims.) The xlsx's +10.24 mean
shift is therefore 2.56 grade points ≈ **20bp cheaper across the book** — real, but v0.1 overstated it.

The actual damage is to differentiation, which is the whole purpose of the group:

| Table | Premium range | Rate spread |
|---|---|---|
| `sector_reference_v1.yaml` (15 industries) | 38.89 – 71.97 | **66bp** |
| xlsx (7 real industries) | 54.29 – 77.86 | **47bp** |
| xlsx (incl. `Others` at 50) | 50.00 – 77.86 | 56bp |

Anchoring at 75 pushes every industry into the top half of the scale and squeezes out a third of the
spread.

*Taxonomy.* Five of the seven map by name (Retail↔Retail Trade, F&B↔Food & Beverage,
Manufacturing↔Manufacturing, Construction↔Construction Materials, Agriculture↔Agriculture & Farming),
but every matched cell moves **up by 10–35 points**. `E-commerce` and `Others` are new; `Services`
collapses IT Services, Professional Services and Education & Training; six yaml rows have no home at
all (Healthcare & Pharmacy, Beauty & Personal Care, Logistics & Transport, Tourism & Hospitality,
Furniture & Woodwork, Textile & Garment).

*The `Sector Growth` column is the one that fails invisibly.* Factor 13 consumes `sector_cagr_pct` —
a raw annual percentage — through a sigmoid with a true midpoint of 0.67% CAGR:

```
cagr_pct =  7.0  ->  78.391      (yaml: Retail Trade)
cagr_pct = 14.0  ->  93.777      (yaml: IT Services)
cagr_pct = 63.0  -> 100.000      (xlsx: Construction)
cagr_pct = 90.0  -> 100.000      (xlsx: E-commerce)
```

Every value in the xlsx's growth column saturates the sigmoid at exactly 100.000. Wire that column to
`sector_cagr_pct` and all eight industries score a perfect 100 on growth, the factor stops
discriminating entirely, and no error is raised. Nothing in either file states which input slot the
column belongs in.

**Issue 2b — The anchor is being moved to dodge a gate that cannot fire.** *(new, v0.2)*

Loc's stated reason for anchoring at 75: *"anchoring at 50 is a lot of factors are gonna be <50,
touching the knockout rules."* Three facts from `gates.py` and `engine.py` say the concern is unfounded:

1. **Gate 3 is `severity: soft`.** `engine.py` resolves `hard → REJECT`, `soft → REVIEW`. Soft gates
   route to the review queue and knock nobody out. Only three gates are hard — excluded industry,
   KYC/AML, CIC floor — and **none of them reads a factor score**. (The gates.py docstring's phrase
   "8 knockout gates" is the likely source of the impression.)
2. **Gate 3 cannot fire under any input today.** It ships `enabled: false` *and* `threshold: null`, and
   `_gate_fires` returns `False` immediately when the threshold is `None`. Two independent off-switches.
3. **The only other score-sensitive gate is gate 8**, which reads `daily_repayment_rate ≥ 0.30` — a
   pricing output, not a factor score. Re-anchoring the sector table does not move it.

So the anchor change buys nothing against the gates and costs 19bp of industry differentiation plus a
golden-set re-baseline. **The correct lever is gate 3's `threshold`**, deliberately left `null` pending
a business decision. Set it to the count of sub-50 factors that genuinely warrants a human look — the
golden set gives the distribution — and it stays a params-file edit, as `gates.py` was written to
guarantee.

Loc's underlying observation is still valid: the median SME scores below 50 on **8 of 22 factors**, and
gate 3 at its drafted thresholds fires on 98.4% of the book. That is the factor-curve calibration
problem (median 96 on Cost Flexibility, 31 on Top-3 Concentration), it is model-wide, it is worth
roughly 110bp on the median rate, and it should wait for real repayment data. It is not a sector-table
edit.

**Issue 3 — Version stamping is not currently possible.** `GradingResult` carries `engine_version` and
`params_version` but **no sector-table version**, and `score_runs` has no column for any of the three.

**Issue 4 — `score_runs.overall_score` is `Numeric(5,2)`.** The rate must derive from the unrounded
grade (core R5). Persist the full-precision grade **and** the rate; treat the column as display-only.

**Issue 5 — `ScoreRun.status` has no state for `INSUFFICIENT_DATA` or `AI_PENDING`.** Extending
`RUNNING → READY → LOCKED` is a shared-model change and needs Phat's agreement per `CLAUDE.md`.

### 2.2 The 21-vs-22 day divergence

`pricing.py` divides by `working_days_per_month: 21`. The repayment spec's `D` defaults to **22**, and
every worked example in §12 uses 22. On the spec's own case — P = 300,000,000, r = 12%, x = 4 months,
T₀ = 312,000,000:

| Source | Days | Daily amount |
|---|---|---|
| `pricing.py` (`target_daily_vnd`) | 84 | **3,714,285** |
| Repayment spec §4.1 (`A₀`) | 88 | **3,545,454** |

**4.76% apart.** The SME is quoted one number at application and signs a contract carrying another. The
schedule is contractual, so `working_days_per_month` moves to 22 — a **params version bump**, since it
changes `target_daily_vnd` and `daily_repayment_rate` on every historical run. Confirmed: at D = 22 the
engine reproduces the spec's `A₀ = 3,545,454` and `N_bs = 118` exactly.

### 2.3 Repayment mechanic

**Issue 6 — "No re-amortize, no rebates" conflicts with spec v1.3 as written.** The spec mandates the
opposite in four places: §4.2 rebuilds total interest and re-spreads the balance; §4.4 and D21 require
a pro-rata uplift rebate and call it load-bearing; INV-15 asserts a full rebate on settlement inside
the original term; EC-22/EC-23 are its edge cases. The instruction is only consistent if **extensions
do not exist in v1** — which they cannot anyway, since §7.3 needs evidence validated against an
e-invoice source and OP-02 records that no acquisition path is chosen. Hence S4. **This must reach the
contract template: a v1 contract must not grant an extension right we have no mechanism to operate.**

**Issue 7 — Money is stored as `Numeric(15,2)` throughout.** Spec §14: *"Money is integer VND
everywhere. No sub-unit. No decimals anywhere in the system."* The distribution splitter in
`payments/service.py` quantizes shares to `0.01` — it allocates hundredths of a đồng. INV-1 is
trivially assertable over integers and permanently fragile over a 2-dp scale. Change **before** any
facility table is written.

**Issue 8 — There is no scheduler.** No ARQ, no cron, nothing in `requirements.txt`. The repayment
mechanic is entirely a daily batch. `CLAUDE.md` lists the ARQ scaffold as "deferred"; it is now on the
critical path.

**Issue 9 — No business-day calendar source (OP-05).** `N₀`, `N_bs` and every `scheduled_date` depend
on a Vietnamese holiday calendar including Tết, which EC-01 forbids deriving from weekday rules.

### 2.4 Money movement

**Issue 10 — The funded state is reachable without money, and disbursement guards on it.**
`market/service.py::place_order` sets `status="FILLED"` and `payment_confirmed_at=now()` on placement,
posts **no ledger transaction**, and increments `funded_amount`. When that reaches target it sets
`listing.status="FUNDED"` and `contract.status="ACTIVE_FUNDED"`. `POST /payments/disbursements` guards
on exactly `listing.status == "FUNDED"`. The chain today:

> unpaid orders → `funded_amount` hits target → FUNDED / ACTIVE_FUNDED → disbursement guard passes →
> a real `DISBURSEMENT` leg posts to the ledger

The ledger's first genuine entry is predicated on money that never arrived. Under S5 that guard is the
only thing between "an investor actually wired us funds" and "we wire funds to an SME". It has to
become real before anyone disburses anything. (GAP-2, still open.)

**Issue 11 — `FUNDING`, `FEE`, `PENALTY` and `REFUND` are valid entry types that nothing has ever
posted.** Only `DISBURSEMENT`, `REPAYMENT` and `DISTRIBUTION` are wired. `record_repayment` distributes
100% of every repayment to lenders pro-rata on principal, so FundLok's revenue model has no
implementation and there is no principal/interest split for investor reporting.

**Issue 12 — No KYC approval endpoint (GAP-1).** Nothing in `app/` ever sets
`Document.status = "APPROVED"`, and `project_has_verified_kyc()` gates `POST /market/listings`. **No
listing can go live.**

**Issue 13 — The marketplace has no read endpoints.** `app/market/router.py` has exactly two routes,
both POST. No `GET /market/listings`, no detail, no portfolio, no holdings. Phat cannot build browse.

**Issue 14 — The expected-loss constant is stale (OP-11).** 2.61%/yr was set against mandate-based
collection; under push-only it is almost certainly too low.

**Issue 15 — `LENDER` account semantics are undefined. BLOCKS T10.** *(new, v0.2)*
`LENDER` accounts are only ever credited by `DISTRIBUTION`, so today a `LENDER` balance reads as
"cash returned to this investor on this contract". No account represents their **outstanding principal
claim**. Adding a `FUNDING` leg forces the choice, and it determines every investor-facing balance we
will ever display. Decide before the first `FUNDING` posting; changing it afterwards means re-deriving
history.

**Issue 16 — Un-deployed investor cash has no account. BLOCKS T10.** *(new, v0.2)*
`LENDER` is contract-scoped (`owner_user_id` + `contract_id`). Under manual bank transfers an investor
will wire funds before choosing a deal, or in excess of one, and that cash has nowhere to sit. Account
types are `OMNIBUS_CASH`, `LENDER`, `BORROWER`, `FL_REVENUE`, `SUSPENSE` — and `SUSPENSE` is
provisioned in shape only, with no handling or sweep logic built against it (ledger spec Open Q#2).
Either add a platform-level investor cash account, or decide `SUSPENSE` becomes it and build the sweep.

**Issue 17 — The industry string is a hard contract between the form and the engine.** *(new, v0.3)*
`_validate_inputs` **raises `ValueError`** when `inputs.industry` is in neither `supported_industries`
nor `excluded_industries`. Not `INSUFFICIENT_DATA`, not a soft failure — an exception that propagates
to the caller. `supported_industries` in `grading_params_v1.yaml` is exactly the yaml's 15 industries,
same spellings ("Food & Beverage", "Agriculture & Farming", "Construction Materials"…). So once T0a's
frontend change lands, **any form submitting an xlsx-style name ("Retail", "Services", "E-commerce")
crashes scoring.** Two consequences:

1. **Serve the list, don't transcribe it.** T3 exposes `supported_industries` over the API so Phat's
   dropdown is generated from the params file. A hardcoded copy in the frontend is the exact drift
   that produced the two-table problem in the first place.
2. **Excluded industries become unreachable from the UI.** `excluded_industries` (gambling, alcohol,
   tobacco, weapons, defence) are deliberately allowed through validation so gate 5 — a *hard* reject —
   can fire after grading. If the dropdown offers only the supported 15, nothing can ever select one
   and gate 5 is dead code from the SME's path. Excluded-industry screening then has to happen in KYB
   against the registered business activity, not at the dropdown. Confirm with Loc which it is.

Check before the FE change ships: any stored `LoanApplication` carrying a non-yaml industry string
will crash on scoring. Nothing is live, so this is probably an empty set — verify rather than assume.

**Not an issue — recorded so it is not "fixed".** There is no balance table and there should not be.
`get_account_balance()` computes `SUM(credits) − SUM(debits)` at read time: *"There is no stored
balance column anywhere to fall out of sync."* If read performance ever bites, that is a materialised
view derived from the entries, never a table anything writes to directly.

---

## 3. Task list

`[D]` marks tasks needed for the 20 Sept demo. Dependencies are hard unless stated.

### Phase 0 — Decisions (no code; unblock in parallel)

| ID | Task | Owner | Blocks |
|---|---|---|---|
| ~~**T0a**~~ | **RESOLVED (Loc, 17 Sep).** `sector_reference_v1.yaml` is the engine table; the xlsx is **not** adopted anywhere, and the **frontend industry list changes to the yaml's 15 industries**. Gate 3 is enabled at **`threshold: 13`** (flags 3.75% of the golden set for review; median SME has 8 of 22 factors below 50). The 75-anchor question is deferred to the factor-curve recalibration, pending real repayment data. | — | — |
| ~~**T0b**~~ | **RESOLVED (Loc, 17 Sep).** `bank_rate_pct` is a **board-set constant, baseline 12.0**, revised at scheduled reviews. It must become a config setting with an effective date — not a dataclass default — and the rate in force must be recorded on every score run so any quote is traceable. | — | — |
| **T0c** | Confirm v1 contracts grant no extension right (S4). | Loc + counsel | Contract template |
| **T0d** | Supply the Vietnamese business-day calendar for 2026–2027 including Tết. | Ops | T8 (production; demo can seed an approximate table) |
| ~~**T0e**~~ | **RESOLVED (Edward, 17 Sep).** Response shapes specified in §5.1. Send to Phat as the contract; changes go through the spec, not chat. | — | — |
| ~~**T0f**~~ | **RESOLVED (Edward, 17 Sep).** Ledger account semantics settled in §5.2. **Two defects in the existing convention surfaced and must be closed by T21 before T10 builds against them.** | — | T21 |

### Phase 1 — Foundations `[D]`

**T1 — Money to integer VND.** `[D]` *No dependencies. Do this first.*
Migrate every money column to `Numeric(20,0)`: `ledger_entries.amount`,
`contracts.target_amount`/`funded_amount`, `listings.target_amount`/`funded_amount`/`min_ticket`,
`orders.amount`, `holdings.principal`, `loan_applications.requested_amount`. Remove the `0.01`
quantize in `payments/service.py`; re-derive the largest-remainder splitter over integers.
*Accept:* ledger tests pass; a 1 VND repayment split across 3 holdings sums to exactly 1; no
`quantize(Decimal("0.01"))` remains under `app/`.

**T2 — ARQ worker scaffold.** `[D]` *No dependencies.*
Settings-driven Redis URL, health task, one job registered at the ICT daily batch window (explicit,
must not straddle midnight, per §14).
*Accept:* worker starts in docker-compose; a no-op daily job fires and logs; timestamps are
`Asia/Ho_Chi_Minh`.

**T3 — Sector reference loader + wire `grade()` into `start_score_run`.** `[D]`
Write `app/underwriting/grading/sector_reference.py` per `sector-reference-table.md` R2 — used by
**production callers assembling a `GradingInput`**, never inside the scoring path (the golden set
supplies its own values and 10,000 rows stop reconciling otherwise). Replace the `72.50 / "B"` mock.
Also in T3, per T0a/T0b: enable gate 3 with `threshold: 13`; move `bank_rate_pct` to a config setting
with an effective date; bump `params_version`. Expose the supported industry list over the API
(Issue 17) — Phat's dropdown must be generated from the params file, never transcribed.
*Accept:* a real application scores to a numeric grade and rate, not `AI_PENDING`; the golden set still
passes 270,000 assertions with 0 failures; `INSUFFICIENT_DATA` produces no grade rather than a low one;
gate 3 fires on 3.7–3.8% of the golden set (`test_gate3_fire_rate_is_instrumented`).
*Depends on:* T0e only. **T0a and T0b are resolved.**

**T4 — Score-run persistence and replay.** `[D]`
Add `engine_version`, `params_version`, `sector_reference_version` and the full-precision grade and
rate (new append-only `score_run_inputs` table, per the ledger pattern — not more JSONB). Add
`sector_reference_version` to `GradingResult`. Extend `ScoreRun.status` with `INSUFFICIENT_DATA` and
`AI_PENDING`.
*Accept:* `test_score_run_persists_full_precision_grade_and_rate`;
`test_score_run_records_engine_and_params_version`; `test_score_run_is_replayable_from_stored_inputs`.
*Depends on:* T3.

**T5 — Align `working_days_per_month` to 22.** `[D]`
Change the param, bump `params_version`, record it in `grading-engine-deviations.md`.
*Accept:* for P = 300,000,000 / r = 12% / x = 4, `target_daily_vnd` equals `A₀ = 3,545,454`.
*Depends on:* T3.

### Phase 2 — Repayment mechanic (spec §4.1, §4.5, §5, §6)

**T6 — Facility data model.** `[D]`
`facility`, `schedule_version`, `scheduled_payment`, `state_transition` per repayment spec §8. Omit
`revenue_submission`, `extension`, `fee_ledger` (S4); `inbound_transfer` moves to T10. All money
`Numeric(20,0)`. DB-level immutability on `backstop_day_index` (INV-10); unique on
`(facility_id, scheduled_date)` (INV-6); unique on `facility.payment_reference` (D20);
`state_transition` append-only.
*Accept:* migration chains off the current Alembic head with a hash revision ID; UPDATE of
`backstop_day_index` raises at the DB layer.
*Depends on:* T1.

**T7 — Origination: schedule generation.** `[D]`
Implement §4.1 exactly. Integer VND, floor division, remainder absorbed **entirely by the final
instalment**. Assert INV-1, INV-5, INV-7, INV-13; each failure halts that facility rather than
continuing.
*Accept:* §12.1 reproduces to the đồng — I = 12,000,000; T₀ = 312,000,000; N₀ = 88; A₀ = 3,545,454;
remainder 48; final 3,545,502; A₀ × 87 + final = 312,000,000; N_bs = 118; implied nominal 12.00%.
**An implementation that does not reproduce these is wrong.**
*Depends on:* T6, T8.

**T8 — Business-day calendar service.** `[D]`
Per-SME calendar, 22-day default, backed by an annual Vietnamese holiday table including Tết.
Non-business days generate no reminder, no expectation, no schedule slot (EC-01). `backstop_date` is
derived and recomputable; `backstop_day_index` never moves (EC-15).
*Accept:* a schedule spanning Tết extends in calendar terms with no extension event and no fee; `N_bs`
is unchanged by a calendar revision.
*Depends on:* T0d for production data; may be built against a seeded table.

**T9 — Facility state machine.** `[D]`
The repayment spec's §5.3 transitions and guards. `DRAFT`, `APPROVED`, `DISBURSED`, `ACTIVE`, `ARREARS_WARNING`,
`ARREARS`, `ACCELERATED`, `IN_RECOVERY`, `SETTLED`, `WRITTEN_OFF`. Omit `UNDER_REVIEW` (S4). Every
transition writes a `state_transition` row with actor and trigger.
*Accept:* INV-4 — nothing sits in `ACTIVE`/`ARREARS` past `N_bs` with a balance; INV-9 — the
transition into `WRITTEN_OFF` is refused while `day_index ≤ N_bs`.
*Depends on:* T6.

### Phase 3 — Money movement

**T10 — Bank movement recorder + reconciler.** `[D]` ***(merges v0.1's T10 and T13)***

One endpoint records a real-world bank movement — amount, value date, bank reference, direction,
counterparty, statement id — and posts the matching ledger transaction through
`ledger.service.post_transaction()`. **Idempotent on the bank's own reference, not a client-supplied
key.** Manual ops entry now (S5) and statement import later are two input adapters over **one code
path**; the temp solution is the permanent reconciler.

- `inbound_transfer` table per §8, with DB-level uniqueness (INV-12, EC-18).
- Matching is on `payment_reference` **only** — never amount or payer name (D20). Unmatched or
  ambiguous goes to an `UNMATCHED` queue: never silently discarded, never auto-applied on a best
  guess (EC-11). Manual attribution records who attributed it.
- **Order funding.** `place_order` creates the order `PENDING_PAYMENT` with its own payment reference
  and posts nothing. A matched movement moves it to `FILLED` and posts a `FUNDING` leg.
  `listing.funded_amount`, `contract.funded_amount`, `listing.status="FUNDED"` and
  `contract.status="ACTIVE_FUNDED"` all move **only** on confirmation (Issue 10). Implement
  `CANCELLED` and `EXPIRED`.
- **Disbursement.** Ops records the outbound movement; the existing `DISBURSEMENT` posting runs behind
  the now-real `FUNDED` guard.
- **Repayment.** Matched inbound applies to the facility: arrears first (EC-04), then the day's
  instalment; partial payments leave the day unsatisfied (EC-03); a lump sum applies forward across
  consecutive days and records every day it satisfied (EC-17); overpayment that clears the balance
  settles and returns the excess, never holding a credit (EC-05).

*Accept:* re-importing the same statement creates no second row and does not double-credit; an order
placed and never paid leaves `funded_amount` at zero and expires;
`test_order_does_not_fill_without_confirmed_payment`; `test_disbursement_refused_when_funding_unconfirmed`;
every posting balances.
*Depends on:* **T0f**, T1, T6, T9.

**T11 — Daily batch: reminders, cutoff, arrears, backstop.** `[D]`
The repayment spec's §6.2 cycle as an ARQ job. Reminder at day open. At cutoff mark days `SATISFIED`/`MISSED` — there is
no `FAILED`, nothing was attempted (D18). Escalate per repayment spec §6.3 with `grace_window` and
`recovery_threshold` as **runtime config** (pilot: 2 business days, 5 × A_current). Evaluate the
backstop daily; on `day_index ≥ N_bs` with a balance, move to `ACCELERATED`, set `cure_period_ends`,
and **keep collecting**.
*Accept:* a facility with no inbound walks ACTIVE → ARREARS_WARNING → ARREARS on schedule; payment
inside the grace window returns it to ACTIVE with no fee and no arrears record; a partial payment
during the cure period reduces the balance but neither extends the cure nor returns it to ACTIVE
(EC-14).
*Depends on:* T2, T9, T10.

**T12 — Emitted events.** `[D]`
The repayment spec's §9 list minus extension and uplift events (S4). Events are facts about the past — never mutated,
never retracted.
*Accept:* `transfer.unmatched` pages someone; `facility.settled` carries actual duration `y` and
whether settlement was on schedule, early, or at acceleration.
*Depends on:* T9, T10.

**~~T13~~ — merged into T10.**

**T14 — Repayment split and the `FEE` leg.** `[D]` *(rewritten, v0.5 — S6)*
Split each repayment into principal, interest and the FundLok fee, and distribute the remainder by
`share_ratio` with largest-remainder absorption over integers (T1).

Per S6 the fee **rate** is config with a default of `0`, but the split path is built now, not deferred.
Deferring it is not "no fee" — it leaves `record_repayment` distributing **100% of every repayment to
lenders**, which is an overpayment, and it means historical transactions have a different leg structure
from later ones, so reporting and reconciliation have to handle both shapes forever.

**At a zero rate, omit the `FEE` leg entirely — do not post a zero-amount one.**
`post_transaction` raises `LedgerImbalanceError("leg amount must be positive")` for any leg with
`amount <= 0`, so a zero fee cannot be represented as a posting. The splitter must therefore handle
"no fee leg" as a first-class case, which is also what makes turning the fee on later a config change
rather than a code change.

The fee is deducted from the investor distribution, never added to the borrower's obligation (S6), so
nothing in T7's `T₀` or INV-5 changes when the rate moves off zero.

*Accept:* legs sum to the repayment exactly at both a zero and a non-zero rate; at rate 0 no `FEE` leg
is written and no zero-amount leg is attempted; at a non-zero rate `FL_REVENUE` is non-zero and the
investor distribution is correspondingly smaller; `T₀` is byte-identical across both;
per-investor principal and interest are separately readable.
*Depends on:* T1, T10, T21.

**T15 — KYC document approval endpoint (GAP-1).** `[D]` *No dependencies. Small, unblocks listing.*
Admin endpoint setting `Document.status = "APPROVED"` with actor, timestamp and rationale via
`app/utils/audit.py`.
*Accept:* a project with approved documents passes `project_has_verified_kyc()` and can be listed.

**T16 — Marketplace and portfolio read endpoints.** `[D]`
`GET /market/listings` (filterable, paginated), `GET /market/listings/{id}`, `GET /market/orders`
(mine), `GET /market/holdings` (mine, with `share_ratio` and balances), `GET /projects/{id}/applications`.
*Accept:* an investor can browse open listings and read their own portfolio without an admin role.
*Depends on:* T0e.

### Phase 4 — Landing-page endpoints (`BackEnd.docx`)

**T17 — `POST /api/sme/indicative-rate`.** `[D]`
**Must not call `grade()`.** `GradingInput` needs 24 months of revenue, COGS, fixed and variable cost,
three concentration ratios, CRR/RRI/TCP, CIC and seven AI scores; the landing page has eleven fields.
Build a separate indicative estimator reusing `pricing.py`'s rate formula and the sector premium only.
Return a **band** (`rateLow`/`rateHigh`, `gradeLow`/`gradeHigh`) plus group scores for ops, and carry
`"indicative": true` with the full version triplet on every response including errors. p99 < 200ms.
*Accept:* the response is never persisted as a `ScoreRun`; the version triplet is always present.
*Depends on:* T3, T4.

**T18 — `POST /api/sme/signup-lead` and `POST /api/investor/enquiry`.** `[D]`
Lead capture before the redirect. The investor enquiry is called twice — on Calculate, and on Sign-up
with `shown_net_apy` — and the second **updates the same record keyed on email**. Store the band shown
with its version triplet. Private intake only. On failure, log and still return the number.
*Accept:* two calls with one email yield one lead row; the shown band is recoverable for any lead.
*Depends on:* T17.

**T19 — `POST /api/investor/yield-estimate`.** `[D]`
Server-side. Amount, commitment, tier, cadence in; loan rate, expected loss, fee, net flat, net APY
out. Expected loss from config, not a literal. Label output indicative pending OP-11.
*Accept:* no pricing constant appears in any client bundle; changing the loss assumption is a config
edit with no client deploy.
*Depends on:* T0b.

### Phase 5 — Verification

**T20 — Spec-conformance test suite.** `[D]`
Every §12 worked example as a test, every §10 invariant as an assertion that fails loudly and halts the
affected facility, every in-scope §11 edge case as a named test. Acceptance criteria map 1:1 to test
function names per `CLAUDE.md`.
*Accept:* §12.1 and §12.4 reproduce to the đồng; INV-1 holds after every posting; a mis-specified rate
is rejected rather than clamped.
*Depends on:* T7, T9, T10, T11.

---

## 4. What can start immediately, and what cannot

**Start now, no decision needed — T1, T2, T15.** Then T6 (needs T1), T9 (needs T6), T7/T8 (needs T6,
calendar can be seeded). That is the integer-money migration, the worker, the KYC unblock, and the
whole facility/schedule core.

**Unblocked as of v0.3 — T3, T4, T5.** T0a and T0b are answered. T0e (response shape with Phat) is the
only remaining gate, and it constrains the API surface rather than the engine work, so T3 can proceed
against the params changes immediately.

**T10 and T14 now wait on T21**, the funding-flow spec, which §5.2 defines. T0f settled the semantics;
T21 turns them into the leg table and closes the two convention defects. Spec first, then build.

**Independent of everything — T17, T18, T19** can run in parallel if someone else takes them.

**For 20 September**, the cut is **T1, T15, T2, T6, T9, T7, T8, T3, T4, T5** — integer money, a real
fixed schedule reproducing Loc's worked example to the đồng, and real pricing behind it. It shows a
bank the two things it will ask about: how we price, and what the borrower owes.

**T10, T11, T14, T16 are the second wave.** Under D18 reconciliation is not a control on top of
collection, it *is* the collection mechanism, and its reliability sets the reliability of arrears, the
backstop, and every investor-facing number downstream. It should not be compressed into three days.

---

## 5. Resolved decisions — T0e and T0f

### 5.1 Response shapes (T0e)

**Conventions, everywhere.** Money is a **string of integer VND** (`"312000000"`) — not a JSON number.
VND amounts sit well inside float53 so this is discipline, not necessity: it stops any client doing
float arithmetic on money by accident and matches the integer-VND rule end to end. Rates and scores
are JSON numbers. Timestamps are ISO-8601 with offset, ICT. Every response that carries a grade or a
price also carries the `versions` block below — including error responses.

```
versions: {
  engine, params, sector_reference,          // strings
  bank_rate_pct, bank_rate_effective_from    // number, date — the rate in force for THIS run
}
```

**`ScoreRunOut`** — returned by `POST /underwriting/score-runs` and its GET.

```
id, application_id, status, created_at, locked_at
decision        APPROVED | REVIEW | REJECT | INSUFFICIENT_DATA | AI_PENDING
grade           { value: number|null, display: number|null }   // full precision, and 2dp for UI
pricing         { interest_rate_pct, target_payment_vnd, target_daily_vnd,
                  avg_daily_revenue_vnd, daily_repayment_rate } | null
premiums        { bcq, rsg, sector, behavioral }
factor_scores   { <22 keys>: number|null }
fired_gates     [ { id, key, severity } ]        // only gates that fired; never fired:false entries
versions        { … }
```

`pricing` and `grade.value` are **`null`** when `decision` is `INSUFFICIENT_DATA` or `AI_PENDING`.
Never `0`, never `0.0` — R8 is explicit that a missing score must not look like a low one, and this is
the single most likely place for that bug to enter through the API rather than the engine.

**Marketplace reads (T16).** `limit`/`offset` with a `total`; cursor paging is not worth it at this
volume.

```
GET /market/listings          -> [ ListingSummary ], filterable by status, industry, grade band
GET /market/listings/{id}     -> ListingDetail
GET /market/orders            -> caller's own orders
GET /market/holdings          -> caller's own holdings

ListingSummary  listing_id, contract_id, status, target_amount, funded_amount,
                min_ticket, open_at, close_at,
                borrower: { industry, company_size, grade_band, interest_rate_pct,
                            duration_months }
ListingDetail   ListingSummary + { daily_amount, total_repayable, schedule_days,
                                   backstop_day_index }
HoldingOut      contract_id, principal, share_ratio, outstanding_claim,
                distributions_received
```

**What investors do not see: `factor_scores`, `premiums`, `fired_gates`.** A grade band and a rate are
what an investor needs to price risk. The 22 factor scores are our model and, for a household
business, arguably personal data about the SME — they belong in ops responses only. `ListingSummary`
carries no SME name, tax code or address.

### 5.2 Ledger account semantics (T0f)

**Issue 15 — `LENDER` means the investor's outstanding claim on that contract**, not cumulative
returns. So `DISTRIBUTION` **debits** `LENDER` (reducing the claim) rather than crediting it.

Why this way round: "cash returned" is trivially recoverable by summing that account's `DISTRIBUTION`
entries, whereas "still owed" is *not* recoverable from a returns-only account, because nothing stores
what the claim started at. It also makes `LENDER` mirror `BORROWER`, which gives a real invariant worth
asserting — the two sides of the contract must net — and that invariant catches distribution bugs that
would otherwise surface as an investor complaint. And it is the number an investor actually asks for.

The ledger spec records **no data in the system** (Open Q#4) and no `FUNDING` leg has ever been posted,
so this costs nothing now and is a repapering exercise later.

**Issue 16 — add a new account type `INVESTOR_CASH`**, platform-level: `owner_user_id` set,
`contract_id` NULL. It holds an investor's confirmed-but-uncommitted cash.

**Do not use `SUSPENSE` for this.** Ledger spec Open Q#2 resolved `SUSPENSE` as *"the structural home
for confirmed-but-unattributed inbound funds"* — which is exactly T10's `UNMATCHED` queue. Putting
uncommitted investor cash there conflates "we know whose this is and it is uncommitted" with "we do not
know whose this is", and reconciliation then cannot tell them apart. That is the one distinction the
whole push-collection model depends on.

Note `account_type` carries a DB `CHECK` constraint listing the five existing types; adding
`INVESTOR_CASH` is a migration, not just a code change.

**Two defects in the existing convention, surfaced by this decision. T21 closes them.**

1. **`BORROWER` settles at −I, not 0.** `DISBURSEMENT` credits `BORROWER` with **P**, but repayments
   debit it with **T = P + I** over the life of the facility. Final balance is `P − T = −I`. The
   account is recording cash delivered while being drained by an obligation, and the two are not the
   same quantity. **Fix: recognise the full obligation `T₀` at origination** — legitimate here
   precisely *because* S4 fixes the total at origination with no re-amortisation, so `T₀` is knowable
   and immutable on day one. The flat-interest decision is what makes the clean treatment available.
2. **There is no external counterparty account**, so money crossing the FBO boundary cannot be
   expressed as a leg at all — every leg needs an internal debit *and* an internal credit. Investor
   cash arriving from outside has nothing to move *from*. T21 decides whether that is an `EXTERNAL`
   clearing account or `OMNIBUS_CASH` acting as the pool contra, and states the reconciliation
   invariant that ties the ledger to the bank statement.

**T21 — Funding-flow spec.** `docs/specs/payments/funding-flow.md`. The full leg table for `FUNDING`,
`DISBURSEMENT`, `REPAYMENT`, `DISTRIBUTION`, `FEE` and withdrawal, under the decisions above; the
reconciliation invariant against the bank statement; and the `INVESTOR_CASH` migration.
**Write this before T10 implements against it.** It is the one place in this handoff where the spec
must precede the code, because the first `FUNDING` posting fixes the meaning of every investor balance
the platform will ever display, and unwinding it means restating history.
*Blocks:* T10, T14.

---

## 6. Out of scope, recorded so it is not inferred

Extensions, the late-repayment uplift and the rebate (§4.2, §4.4, §7 — S4). Revenue-evidence
acquisition (OP-02). Tamper and fraud controls on revenue evidence (deferred 27 Aug 2026). Share
conversion. Withdrawal and reinvestment. Compliance reporting. Escrow provisioning (S1 — the
`scope='CONTRACT'` seam stays dormant). A stored balance table (see §2.4). Document ingest and
parsing, which remains the largest gap between here and production. Frontend — Phat owns all of it.
