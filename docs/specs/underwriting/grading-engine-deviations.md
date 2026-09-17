# Grading Engine — Deviations Register

| Field | Value |
|---|---|
| **Status** | LIVING DOCUMENT — not a spec, not a spec gate |
| **Owner** | Edward |
| **Related specs** | `grading-engine-core.md`, `grading-engine-integration.md` |
| **Version** | 1.0 |
| **Date** | 2026-07-28 |

---

## Why this exists

Every place the implementation departs from *FundLok Underwriting Engine — Backend Requirements
v0.2 (27 July 2026)* or from `CLAUDE.md` is recorded here, with a reason and an owner.

Two rules govern it:

1. **A deviation that is not in this register does not exist.** Per `CLAUDE.md`, if it is not written
   down it is not real. An undocumented departure from the CEO's spec is how an underwriting engine
   quietly stops being defensible.
2. **This register is deliberately NOT a spec gate.** `_TEMPLATE.md` requires all §9 Open Questions
   closed before a spec reaches ACCEPTED. That rule is right for design ambiguity but wrong here —
   these items are config-switchable or raise loudly, so none blocks correct implementation, and
   holding the spec at REVIEW until Loc answers all of them would stall the end-to-end platform for
   no engineering benefit. Spec 1 may proceed to ACCEPTED with items open **in this register**.

**Resolution target: after the first end-to-end lending flow is demonstrable.** Not before.

### Status key

| Status | Meaning |
|---|---|
| `DOC-FIX` | Implementation is correct; the requirements doc is wrong and should be corrected |
| `DELIBERATE` | We knowingly differ. No further action unless someone objects |
| `OPEN` | Needs a decision from a named owner. Behaviour is safe in the meantime |

---

## A. Requirements doc is wrong — implementation is correct

These need a correction to the CEO's document so it stops misleading the next reader. No code change.

| ID | Area | Requirements v0.2 says | Verified truth (workbook, 10,000 rows) | Status |
|---|---|---|---|---|
| D1 | Curve form (§3.2) | `score = Upper / (1 + e^(−Steepness·(x − Midpoint)))`, with a "Midpoint" column | `Upper / (1 + e^(±(Steepness·x − Intercept)))`. The "Midpoint" column holds the **intercept**; true midpoint is `Intercept/Steepness`. This single error made six factors appear broken | `DOC-FIX` |
| D2 | Factors 5, 6 (§3.2) | Loan/Revenue `102 / 11.52 / 3.7`; SCSR `100 / 8 / −0.7` | Loan/Revenue `103.50079 / 5.57453 / 3.65945`; SCSR `140.93813 / 0.468868 / 1.10159`. The doc's values, and the workbook's own `Cashflow` tab, are abandoned fits that do not match their own band tables | `DOC-FIX` |
| D3 | RSG roll-up (§3.4) | "Volatility ⅓, Trend ⅓, Seasonality ⅓" | Seasonality carries **¼**. Core sums to 0.91666…, not 1.0 | `DOC-FIX` |
| D4 | Behavioral roll-up (§3.4) | "CIC + Tax Discipline as the core" | **CIC alone at full weight (1.0).** Tax Discipline is absent from the workbook roll-up entirely — its removal in v0.2 was correct, but §3.4 was not updated to match | `DOC-FIX` |
| D5 | Concentration Top 3 (§3.2) | Sigmoid `105 / −0.07 / 3.99` | Linear `100 − x`, same as Top 1. The sigmoid exists on a reference tab but the production column does not use it | `DOC-FIX` |
| D6 | CIC scoring (§3.2) | "lookup band on CIC (e.g. 800→100 …)" | Sigmoid `102.19808 / 0.0139371 / 8.52444`, true midpoint ≈ 611.6 | `DOC-FIX` |
| D7 | Owner Withdrawal (§3.2) | "lookup band on (owner salary + profit distributed) / net profit" | Cubic polynomial `122.05387x³ − 253.24675x² + 27.67557x + 102.65873`, clamped | `DOC-FIX` |
| D8 | Total-duration revenue (§2.3) | "revenue/profit over the loan term window" — ambiguous | `average monthly revenue × duration_months`. An average projected over the term, **not** the trailing N actual months | `DOC-FIX` |
| D9 | Revenue Trend (§3.2) | "avg YoY month-over-month growth" | Mean of **ten overlapping 3-month windows**, each vs the same window 12 months earlier | `DOC-FIX` |
| D10 | Revenue Volatility (§3.2) | "StdDev / Mean of monthly revenue" | **Population** standard deviation (`STDEV.P` / `statistics.pstdev`), not sample. Over the trailing 12 months only | `DOC-FIX` |
| D11 | Cost mapping (§2.1) | "Variable Cost ← Code 11 (COGS) + Code 25 (selling expense)" | COGS is a **separate persisted field**. `total_cost = COGS + fixed + variable-excl-COGS`, and Gross Margin uses COGS alone | `DOC-FIX` |
| D12 | Golden set size (§6) | "1,748 synthetic SMEs" | 10,000 populated rows | `DOC-FIX` |
| D13 | Worked examples (§6) | SME-0001: loan 3,000,000,000 / 3 months / daily repay 73.90% | The grade (70.98) comes from a row with an **800,000,000 / 9-month** loan. The workbook's pricing columns are computed on a stale, different dataset — 9,938 of 10,000 rows disagree on loan size and term. The four worked examples pair one SME's grade with another's loan | `DOC-FIX` |

**Consequence of D13:** the golden set validates grades but **cannot** validate pricing or repayment.
Any Gate 8 (daily repayment rate) statistic derived from that workbook is meaningless. Pricing is
tested against closed-form arithmetic instead.

---

## B. Deliberate deviations

| ID | Area | Convention / spec says | What we do | Why | Status |
|---|---|---|---|---|---|
| D14 | Async (`CLAUDE.md`) | "All service functions are `async def`" | Grading core is synchronous `def` throughout | The rule is correct for anything touching the DB; the core is pure arithmetic (~35µs, nothing awaitable). A CPU-bound coroutine holds the event loop exactly like a sync call while *looking* like it yields. Sync is also an enforceable purity claim — `test_grading_package_has_no_async_def` guards it. **Approved by Edward, 28 July 2026.** Rule to add to `CLAUDE.md`: async is for I/O boundaries, not house style | `DELIBERATE` |
| D15 | Decision states (§1.1) | `APPROVED / REVIEW / REJECT` | Adds `INSUFFICIENT_DATA` and `AI_PENDING` | §2.5 is explicit that missing data must not read as a low score, and §3.3 allows AI factors to be pending. Both are real states an application sits in; neither is one of the three | `DELIBERATE` |
| D16 | Premium clamping (Appendix item 2) | Open question — clamp at 100? | Do **not** clamp. Assert instead | No premium exceeds 100 anywhere in the golden set (max: BCQ 98.46, RSG 92.37, Sector 82.65, Behavioral 96.03), so a clamp is a no-op today. If one ever does exceed 100 we want a red test, not a silent truncation | `DELIBERATE` |
| D17 | Pricing cap (§4.2) | `min(20%, BankRate + (20 − BankRate) × …)` | Same formula; `bank_rate_pct >= 20` raises `ValueError` | The `min()` is unreachable while BankRate < 20. If BankRate is ever configured ≥ 20 the formula prices every borrower at exactly the cap, which is a config error, not a valid state | `DELIBERATE` |
| D18 | Bank rate (§2.4) | "default 12.0%, configurable" | Per-**application** input, defaulting to 12.0 | The workbook's `Raw` tab varies it 8.1–13.6 across rows. Pinning it globally would misprice historical replays | `DELIBERATE` — **superseded by D28, 17 Sep 2026** |
| D28 | Bank rate source (T0b, HANDOFF-03) | D18: per-application input, 12.0 default | Board-set constant with an effective date, in `bank_rate_config` (`app/underwriting/models.py`), not a `GradingInput` dataclass default. The rate in force is recorded on every score run | T0b (Loc, 17 Sep 2026): `bank_rate_pct` is board-set, revised at scheduled reviews, and any quote must be traceable to the rate in force at scoring time -- a dataclass default cannot express "in force as of a date" or be audited after the fact | `DELIBERATE` |
| D29 | `target_daily_vnd` integer rounding (T5, HANDOFF-03) | T5 acceptance criterion: "for P=300,000,000/r=12%/x=4, `target_daily_vnd` equals A0 = 3,545,454" | `pricing.py`'s `target_daily_vnd` is continuous Decimal division (`target_payment_vnd / (duration_months * working_days_per_month)`), giving 3,545,454.545454... -- it does not floor or absorb a remainder into a final instalment. `math.floor()` of it equals 3,545,454, matching the criterion's *value*, but the field itself is not integer-equal to it | Deliberate, predates this task (R4/R10, `pricing.py`'s own docstring): `target_daily_vnd` here is an *indicative* number for grading/pricing, not the literal per-day amount a facility bills. That exact computation (`A0 = floor(T0/N0)`, remainder absorbed by the final instalment) is `app/repayment_schedule/origination.py`'s job (repayment spec §4.1), run once a contract is created -- not the grading engine's. Changing `pricing.py` to floor was out of T5's stated scope ("Align `working_days_per_month` to 22") and risks the "no change to `grade()`/scoring maths" boundary the sector-reference spec's R2 protects. Flagged rather than silently changed | `DELIBERATE` -- **flagged for Edward's confirmation that pricing.py's indicative/estimate framing, not exact-integer matching, is what T5's criterion actually intended** |

---

## C. Open — needs a decision

Safe in the meantime. Each has a defined interim behaviour so nothing is blocked.

| ID | Question | Interim behaviour | Owner | Target |
|---|---|---|---|---|
| D19 | **Gate 3 threshold.** Doc says "≥4 of 22 below 50"; workbook says "≥3". On the golden set these fire on **95.2%** and **98.4%** of applications respectively. Median SME has 8 of 22 below 50. Needs to be a proportion, or crucial-factors-only, or a much higher count | Gate **disabled** in `grading_params_v1.yaml`. Config-switchable, no code change | Loc | Post-E2E |
| D20 | **CIC scale.** Doc cites both 0–700 and 150–750. Workbook generator says 150–750; observed range 442–750; reference band table anchors to 800. Gate 7 is a final, non-overridable reject at ≤500 | Gate 7 **disabled**. Scoring sigmoid still applied (fits the band table well) | Loc | Post-E2E |
| D21 | **`profit ≤ 0`.** Doc is silent. On the SCSR curve a negative ratio scores ≈100 — a loss-making SME would be *rewarded* | `grade()` raises `ValueError`. Fails loudly rather than scoring wrongly | Loc / Edward | Post-E2E |
| D22 | **`owner_withdrawal` input scale.** YAML defines a cubic over a 0–1 ratio, but the golden set supplies this factor as an already-computed 0–100 score, so the cubic is unexercised by the fixture | Accept a 0–100 score, as the fixture does. Cubic retained in params for when the raw ratio is available | Loc | Post-E2E |
| D23 | **`risk_grade` letter vs number.** `ScoreRun.risk_grade` is `Text` and the mock writes `"B"`, but requirements are explicit: "0–100 nominal (no letter grades)" | Leave the column untouched; spec 1 does not write it | Edward | Spec 2 |
| D24 | **Grade precision in the DB.** `score_runs.overall_score` is `Numeric(5,2)` and truncates 70.98376463 → 70.98. Recomputing the rate from that column drifts the target payment by hundreds of thousands of VND on a 3bn loan | Spec 1 returns full precision and never persists. Spec 2 must store the unrounded grade **and** the rate, and never recompute the rate from `overall_score` | Edward | Spec 2 |
| D25 | **Counterparty data source.** Concentration Top 1/Top 3 and RTI (CRR, RRI, TCP) need an invoice-level customer ledger. None of the four sources in §2.1 provides one; the workbook supplies them as pre-graded 0–100 values | Treated as optional inputs. `None` contributes 0 as a bonus — no blocking | Loc | Post-E2E |
| D26 | **Sector group at launch.** Six of seven Sector factors are AI-graded and rubrics do not exist. Sector is 25% of the grade, so 86% of a quarter of the score is unavailable | `AI_PENDING` when absent; deterministic premiums still returned. Options when addressed: static per-industry table, or reweight | Loc / Edward | Post-E2E |
| D27 | **AI rubrics** for the six Sector factors and Founder Experience | Interface built, prompt held in config, scores supplied as inputs | Loc | Post-E2E |

---

## D. Not affected by the custody decision

Recorded because it is a reasonable thing to wonder about while bank partnerships are unresolved.

The custody model — FBO/omnibus vs per-project escrow, **ADR-003** — has **no bearing on this
engine.** Grading consumes an application's financials and produces a grade, a price and a repayment
schedule. It never touches an account, a balance or a fund movement. Both specs here can be built,
merged and tested to completion with the custody question entirely open.

The one adjacency worth noting: the repayment figures the engine emits (target payment, target daily
repayment) become contract terms, and contract terms eventually drive ledger postings. But *which
account* the money sits in is downstream of that, behind the seam ADR-003 already defines. Nothing
here needs to change when the partnership lands.

Relevant to the end-to-end goal: `app/banking/` is already mocked indefinitely pending a partner
decision (`CLAUDE.md`, `docs/specs/banking/account-linking-mock.md`), and the ledger foundation is
merged (PR #18). So a full apply → grade → contract → list → fund → disburse → repay → distribute
walkthrough is reachable **without** resolving custody, using mocked money movement throughout.

Note also that spec 1 R10 already emits the flat-rate repayment schedule the requirements specify
(target payment, target daily repayment, daily repayment rate). A separate `app/repayment_schedule/`
amortisation engine may not be on the critical path for the first end-to-end demo — worth confirming
before scoping it.

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Edward | Initial register. 27 items: 13 doc-fix, 5 deliberate, 9 open. Sync deviation (D14) approved by Edward. |
