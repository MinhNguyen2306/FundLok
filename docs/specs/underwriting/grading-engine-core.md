# Spec: Grading Engine — Deterministic Core

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) — delegable to an implementing model |
| **Module** | `app/underwriting/grading/` |
| **Version** | 1.0 |
| **Date** | 2026-07-28 |
| **Related ADR** | — (candidate ADR-008: pure functional grading core, see §6 R1) |
| **Depends on** | Nothing. Deliberately zero dependencies on `app/` — see §6 R1. |
| **Deviations** | `grading-engine-deviations.md` — read before changing any constant here |
| **Source of truth** | `FundLok formula factors v0.xlsx`, tab `Scoring From Raw`, cols AI–BO |

---

## 1. Context & Goal

FundLok assigns every SME loan application a 0–100 risk grade that sets its interest rate and its
marketplace listing. Today `app/underwriting/service.py::start_score_run` returns a hardcoded mock
(`overall_score = 72.50`, `risk_grade = "B"`, `factor_results = {"mock": True}`). Nothing real is
computed. Until it is, no application can be priced and no listing can carry a defensible number.

The CEO's requirements doc (v0.2, 27 July 2026) specifies 22 factors rolled into 4 group premiums
and a final grade. That document mis-transcribes the scoring curve and is internally inconsistent in
several places; the workbook is authoritative and has been reconciled against all 10,000 of its rows.
See §6 R2 and §9.

**Goal:** a pure, deterministic, replayable grading core — 22 factor scores → 4 group premiums →
final grade → price → repayment schedule → knockout decision — that reproduces the workbook exactly
and has no I/O of any kind.

---

## 2. Out of Scope

This spec covers **calculation only**. The following belong to
`docs/specs/underwriting/grading-engine-integration.md` (spec 2, DRAFT):

- Persisting results to `score_runs`; any change to `ScoreRun`, `LoanApplication`, or migrations.
- The `POST /underwriting/score-runs` endpoint and its Pydantic layer.
- Replacing the mock in `service.py::start_score_run`.
- Routing to marketplace / manual-review queue.
- Audit records via `app/utils/audit.py`.
- ARQ job wiring.

Also out of scope entirely:

- **Document ingest and parsing** (VAT declarations, Form B02-DN, CIC PDF). The core takes an
  already-normalised input object. Parsers are a separate future spec.
- **Calling any AI service.** Six sector factors and Founder Experience are AI-graded; this core
  receives them as already-committed 0–100 numbers. See §6 R3.
- **The investor-facing pros/cons summary.** Separate service, separate spec.
- **ML / decision-forest scoring.** This is the rules engine it will eventually be trained against.

---

## 3. Data Model

**No database changes. No tables. No migrations.** This spec adds no schema and touches no ORM model.

### New package

```
app/underwriting/grading/
├── __init__.py           # public surface: grade(), GradingInput, GradingResult, load_params
├── types.py              # frozen dataclasses for input/output
├── params.py             # YAML loader → frozen ParamSet; fails loudly on drift
├── curves.py             # sigmoid / linear / cubic primitives
├── derive.py             # ingested fields → 11 derived raw metrics
├── factors.py            # 22 factor scores
├── rollup.py             # 4 premiums + final grade
├── pricing.py            # interest rate, target payment, repayment, daily rate
├── gates.py              # 8 knockout gates + decision resolution
├── engine.py             # orchestrator: the only function callers need
└── params/
    └── grading_params_v1.yaml   # ALREADY WRITTEN — do not edit, do not retype
```

### Input type (typed pseudocode)

```
GradingInput  (frozen)
├── company_code                    str
├── industry                        str          must be in params.supported_industries
├── company_size                    Literal["micro","small","medium"]
├── loan_size_vnd                   Decimal      200_000_000 … 5_000_000_000
├── duration_months                 int          one of 3, 6, 9, 12
├── operating_months                int          ≥ 0
├── monthly_revenue                 tuple[Decimal, ...]   EXACTLY 24 values, m1 … m24
├── cogs_y1                         Decimal
├── fixed_cost_y1                   Decimal
├── variable_cost_excl_cogs_y1      Decimal
├── conc_top1_pct                   float | None   0–100
├── conc_top3_pct                   float | None   0–100
├── crr                             float | None   0–100
├── rri                             float | None   0–100
├── tcp                             float | None   0–100
├── sector_cagr_pct                 float          e.g. 14.4 means 14.4%
├── ai_scores                       Mapping[str, float]   keys: regulatory, input_cost_vol,
│                                                          cyclicality, competitor, macro,
│                                                          uncontrollable, founder — each 0–100
├── owner_withdrawal                float | None   see §9 Q5
├── cic_score                       int            150–750
├── kyc_aml_passed                  bool
├── fraud_flags                     tuple[str, ...]
└── bank_rate_pct                   float          per-application; default 12.0
```

### Output type

```
GradingResult  (frozen)
├── engine_version        str            from params
├── params_version        str            from params
├── derived               Mapping[str, float]     all 11 derived metrics, for audit
├── factor_scores         Mapping[str, float | None]   22 keys; None = not scorable
├── premiums              {bcq, rsg, sector, behavioral}   float
├── final_grade           float          FULL precision — do NOT round
├── interest_rate_pct     float          FULL precision
├── target_payment_vnd    Decimal
├── target_daily_vnd      Decimal
├── avg_daily_revenue_vnd Decimal
├── daily_repayment_rate  float
├── fired_gates           tuple[GateResult, ...]
└── decision              Literal["APPROVED","REVIEW","REJECT","INSUFFICIENT_DATA","AI_PENDING"]
```

---

## 4. API Contract

**None.** This spec adds no endpoint. The public surface is one Python function:

```python
from app.underwriting.grading import grade, load_params, GradingInput, GradingResult

params = load_params()                    # or load_params(path=...) in tests
result: GradingResult = grade(inputs, params)
```

`grade()` is **synchronous**. See §6 R1 for why this is a deliberate departure from the
"all service functions are `async def`" convention in `CLAUDE.md`.

---

## 5. State Machine

This spec introduces no status field. It **computes** a decision; it does not persist or transition
anything. For context, the existing machine this feeds (unchanged by this spec):

```
ScoreRun:  RUNNING ──► READY ──► LOCKED
```

The five values in `GradingResult.decision` are a computed classification, not a stored state.
Mapping them onto `ScoreRun.status` is spec 2's problem.

---

## 6. Business Rules

### R1 — The core is pure. This is the rule everything else depends on.

`app/underwriting/grading/` must import **nothing** from `app/` and must perform **no I/O**.
Specifically forbidden inside the package:

- Any database access. No `AsyncSession`, no `select()`, no `get_db`.
- Any network call, file read at call time, or environment variable read.
- `datetime.now()`, `uuid4()`, `random`, or anything else non-deterministic.
- Any logging that includes a timestamp or changes behaviour.

Everything the core needs is passed in. `load_params()` is the single exception — it reads the YAML
once, at import or on explicit call, and returns a frozen object; `grade()` itself never touches disk.

All functions are plain `def`, not `async def`. `CLAUDE.md` requires async service functions, and
that rule is correct for anything touching the DB — but this is CPU-bound arithmetic with no
awaitable inside it, and wrapping it in a coroutine would add scheduling overhead and hide its purity.
**The async boundary lives in `app/underwriting/service.py` (spec 2), which awaits the DB and calls
`grade()` synchronously.** Do not make the core async.

Why this matters beyond tidiness: the same inputs plus the same `params_version` must produce the
same grade forever, so any past decision can be reconstructed and defended. A pure function gives us
that for free. It also means the golden-set test suite needs no database, no fixtures, and no event
loop.

### R2 — The YAML is the source of truth. Never retype a constant.

`app/underwriting/grading/params/grading_params_v1.yaml` is already written and validated. Every
curve constant, weight and threshold lives there.

- Do **not** copy numbers out of it into Python literals.
- Do **not** "simplify", round, or reformat any value.
- Do **not** consult the requirements PDF for any number. It mis-transcribes the curve form (see
  below) and disagrees with the workbook on at least six factors.

The curve form is:

```
score = min(100, max(0, upper / (1 + exp(sign * (steepness * x - intercept)))))
    sign = +1  when decreasing: true    (higher raw value = worse)
    sign = -1  when decreasing: false   (higher raw value = better)
```

`intercept` is **not** a midpoint. True midpoint = `intercept / steepness`. The requirements doc put
the intercept in a column labelled "Midpoint", which made six factors look broken when they were not.
If a curve seems wrong, re-read this rule before changing anything.

### R3 — AI-graded factors are inputs, never computed here.

Seven factors (`regulatory`, `input_cost_vol`, `cyclicality`, `competitor`, `macro`,
`uncontrollable`, `founder`) arrive as committed 0–100 numbers in `GradingInput.ai_scores`. The core
never calls an LLM. If any is missing, the result decision is `AI_PENDING` (see R8) — the
deterministic premiums are still computed and returned.

### R4 — Float for scores, Decimal for money. The boundary is explicit.

The workbook computes in IEEE double precision, and reproducing it to 1e-7 requires float. So:

- Derived metrics, factor scores, premiums, `final_grade`, `interest_rate_pct`,
  `daily_repayment_rate` → `float`.
- `loan_size_vnd`, `target_payment_vnd`, `target_daily_vnd`, `avg_daily_revenue_vnd` → `Decimal`.

Convert once, at the boundary, and never round an intermediate.

### R5 — Full precision to the edge. Round only for display.

`final_grade` for the first golden row is `70.98376463`, not `71`. The interest rate derives from the
unrounded grade: `12 + 8 × (100 − 70.98376463)/100 = 14.32129883%`. Rounding the grade first gives
14.32 and a target payment that is wrong by hundreds of thousands of VND on a 3bn loan.

Note for spec 2: `score_runs.overall_score` is `Numeric(5,2)` and will truncate the grade to two
decimals. The full-precision grade and rate must therefore also be written into
`score_runs.factor_results` (JSONB), and the rate must be **persisted**, never recomputed from the
truncated column.

### R6 — Derivations, exactly as the workbook does them.

Three of these are counter-intuitive; all are confirmed against 10,000 rows.

1. `revenue_y1 = sum(m13 … m24)` — the most recent 12 months. `m1 … m12` is the prior year.
2. `total_cost = cogs_y1 + fixed_cost_y1 + variable_cost_excl_cogs_y1`. COGS is its own field —
   it is **not** folded into variable cost.
3. `cost_flexibility_pct = (cogs_y1 + variable_cost_excl_cogs_y1) / total_cost × 100`.
4. **"Total-duration revenue" is `avg_monthly_revenue × duration_months`** — an average projected
   over the term, *not* the trailing `duration_months` actual months.
   `loan_revenue_ratio = loan_size / (avg_monthly_revenue × duration_months)`.
5. Likewise `scsr_ratio = loan_size / ((avg_monthly_revenue − avg_monthly_cost) × duration_months)`.
6. **Volatility uses population standard deviation** (`statistics.pstdev`, Excel `STDEV.P`), not
   sample. Over `m13 … m24` only.
7. **Revenue Trend is the mean of ten overlapping 3-month windows**, each compared with the same
   window twelve months earlier. For `k = 0 … 9`:
   `(sum(m[13+k … 15+k]) − sum(m[1+k … 3+k])) / sum(m[1+k … 3+k])`.
   The result is a decimal fraction; the scoring step multiplies by 100. It is *not* a mean of
   twelve monthly year-on-year ratios.
8. `seasonality_ratio = max(m13 … m24) / min(m13 … m24)`.
9. `rti = 0.5·crr + 0.3·rri + 0.2·tcp`, with all three on a 0–100 scale; the scoring step divides
   by 100.

### R7 — Roll-up. Two details contradict the requirements doc; the YAML is right.

```
bcq        = 0.20·GM + 0.20·CM + 0.20·OM + 0.20·CF + 0.10·LR + 0.10·SCSR
rsg        = (1/3)·VOL + (1/3)·TREND + (1/4)·SEAS + TOP1/20 + TOP3/20 + RTI/20
sector     = mean of its 7 factors (1/7 each)
behavioral = CIC + OWNER_WITHDRAWAL/20 + FOUNDER/20
final      = 0.40·bcq + 0.25·rsg + 0.25·sector + 0.10·behavioral
```

- **Seasonality carries 1/4, not 1/3.** The RSG core therefore sums to 0.91666…, not 1.0. This is
  deliberate in the workbook. Do not "fix" it.
- **CIC carries full weight (1.0) in the Behavioral core**, not a share. Tax Discipline is absent
  from the roll-up entirely; its removal in requirements v0.2 was correct. Requirements §3.4 still
  says "CIC + Tax Discipline as the core" — that line is stale. Data Reliability is likewise excluded.
- Bonus factors contribute `score / 20`, i.e. 5% of the factor score as points on top.
- Premiums are **not** clamped in the workbook. Empirically none exceeds 100 across all 10,000 rows
  (max: bcq 98.46, rsg 92.37, sector 82.65, behavioral 96.03), so a clamp would be a no-op. Do not
  add one — if a premium ever exceeds 100 we want the test suite to tell us, not a silent clamp.

### R8 — Missing data produces a state, never a low score.

Return `INSUFFICIENT_DATA` when any of the following holds — and compute nothing further:

- fewer than 24 monthly revenue values, or any is `None`
- `revenue_y1 == 0` (every margin divides by it)
- `total_cost == 0` (cost flexibility divides by it)
- `min(m13 … m24) == 0` (seasonality divides by it)
- `cic_score` is `None`
- `kyc_aml_passed` is `None`

Return `AI_PENDING` when the deterministic factors are all scorable but one or more of the seven
AI-graded scores is absent. Premiums and the grade are still returned, with the missing factors as
`None` and their groups computed over the factors present.

Bonus factors (`conc_top1`, `conc_top3`, `revenue_type`, `owner_withdrawal`) may be `None` without
blocking anything. A `None` bonus contributes 0, which is the correct semantics for a bonus.

### R9 — Gates run after grade and price, and two ship disabled.

| # | Gate | Severity | Rule |
|---|---|---|---|
| 1 | `operating_history` | soft | `operating_months < 24` |
| 2 | `history_vs_term` | soft | `duration_months > 0.25 × operating_months` |
| 3 | `low_factor_count` | soft | **DISABLED** — see §9 Q1 |
| 4 | `first_loan_tenor` | n/a | enforced in the application UI, not here |
| 5 | `excluded_industry` | hard | industry in gambling, alcohol, tobacco, weapons, defence |
| 6 | `kyc_aml` | hard | `not kyc_aml_passed` or `fraud_flags` non-empty |
| 7 | `cic_floor` | hard | **DISABLED** — `cic_score <= 500`; see §9 Q2 |
| 8 | `daily_repayment_rate` | soft | `daily_repayment_rate >= 0.30` |

Resolution: any hard gate fired → `REJECT`. Else any soft gate fired → `REVIEW`. Else → `APPROVED`.

Gates 3 and 7 are `enabled: false` in the YAML and must be read from there, not hardcoded. Both must
be switchable by config alone, with no code change.

Gate 3 is disabled because at the specified threshold it fires on **98.4%** of the golden set (95.2%
at "4 or more"). The median SME has 8 of 22 factors below 50. Shipping it would route essentially the
entire book to manual review.

Gate 7 is disabled because it is a final, non-overridable reject and the CIC scale is unconfirmed.

### R10 — Pricing and repayment.

```
interest_rate_pct     = min(20.0, bank_rate_pct + (20 − bank_rate_pct) × (100 − final_grade) / 100)
target_payment_vnd    = loan_size × (1 + interest_rate_pct/100 × duration_months/12)
target_daily_vnd      = target_payment_vnd / (duration_months × 21)
avg_daily_revenue_vnd = revenue_y1 / 252
daily_repayment_rate  = target_daily_vnd / avg_daily_revenue_vnd
```

`bank_rate_pct` is per-application, defaulting to 12.0 from config. It is **not** a constant — the
workbook varies it 8.1–13.6 across rows. If it is ever configured ≥ 20, `grade()` must raise
`ValueError`, not silently price every borrower at the 20% cap.

**The golden set cannot validate this section.** The workbook's pricing columns are computed from a
stale, different dataset than its grade columns — 9,938 of 10,000 rows disagree on loan size and
term. Test pricing against the closed-form arithmetic above and the worked example in §8, not
against the fixture's pricing columns (which is why the fixture does not include them).

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Fewer than 24 monthly revenue values | No scoring attempted | `GradingResult` with `decision="INSUFFICIENT_DATA"`, all `factor_scores` `None` |
| `revenue_y1`, `total_cost`, or `min(m13…m24)` is 0 | No scoring attempted — division would be undefined | as above |
| `cic_score` or `kyc_aml_passed` is `None` | No scoring attempted | as above |
| One or more AI scores absent | Deterministic factors scored; affected group averaged over present factors only | `decision="AI_PENDING"`, missing factors `None` |
| A bonus factor is `None` | Contributes 0 to its group | normal result, that factor `None` |
| **`profit ≤ 0`** (so `scsr_ratio` is negative or undefined) | `raise ValueError` — see §9 Q3. Do **not** score it; a negative ratio scores ~100 on this curve, i.e. a loss-making SME would be rewarded | exception propagates to spec 2's service layer |
| `duration_months` not in {3,6,9,12} | `raise ValueError` | exception |
| `loan_size_vnd` outside 200m–5bn | `raise ValueError` | exception |
| `industry` not in `supported_industries` | `raise ValueError` | exception |
| `bank_rate_pct >= 20` | `raise ValueError` | exception |
| Any factor score outside [0,100] after clamping | `raise AssertionError` — indicates a params or code bug | exception |
| A group premium exceeds 100 | `raise AssertionError` — do not clamp, see R7 | exception |
| YAML `params_version` differs from the value pinned in the test suite | Test fails loudly | — |

---

## 8. Acceptance Criteria

These become pytest function names, under `tests/underwriting/`. Fixtures are already in place:
`tests/underwriting/fixtures/golden_set.csv.gz` (10,000 rows) and `golden_set_sample.csv` (500 rows,
stratified across the grade range). Each row carries its inputs plus `expect_*` columns for all 22
factor scores, 4 premiums and the final grade, extracted from the workbook.

**Comparison tolerance: `abs(actual − expected) <= max(1e-6, abs(expected) * 1e-7)`.**

### The one that matters most

- [ ] `test_golden_set_full_reconciles_all_10000_rows` — for every row in `golden_set.csv.gz`, all 22
      factor scores, all 4 premiums and the final grade match within tolerance. **This test passing
      is the definition of done.** It currently passes for the reference implementation; if it fails,
      the implementation is wrong, not the fixture.

### Curves and params

- [ ] `test_params_load_and_freeze` — `load_params()` returns a frozen structure; mutation raises
- [ ] `test_params_version_pinned` — `params_version == "wb-v0-20260728"`; guards silent YAML drift
- [ ] `test_sigmoid_decreasing_direction` — a `decreasing: true` factor scores lower as x rises
- [ ] `test_sigmoid_increasing_direction` — a `decreasing: false` factor scores higher as x rises
- [ ] `test_sigmoid_true_midpoint_is_intercept_over_steepness` — at `x = intercept/steepness`, score
      is `upper/2` before clamping
- [ ] `test_all_factor_scores_within_0_100` — across the full golden set, no score escapes the clamp
- [ ] `test_upper_above_100_is_clamped_not_truncated_in_params` — factors with `upper` > 100 still
      return ≤ 100, and the YAML value is unchanged
- [ ] `test_cubic_owner_withdrawal_matches_band_anchors` — cubic at x=0.2 → ≈99.0, x=1.0 → 0

### Derivations

- [ ] `test_revenue_y1_is_sum_of_m13_to_m24`
- [ ] `test_total_cost_includes_cogs_as_separate_field`
- [ ] `test_total_duration_revenue_is_avg_monthly_times_term` — explicitly *not* trailing N months
- [ ] `test_volatility_uses_population_stdev_not_sample` — asserts the two differ and we match `.P`
- [ ] `test_revenue_trend_uses_ten_overlapping_three_month_windows`
- [ ] `test_seasonality_is_max_over_min_of_trailing_twelve`
- [ ] `test_rti_composite_weights_are_50_30_20`

### Roll-up

- [ ] `test_rsg_seasonality_weight_is_one_quarter_not_one_third`
- [ ] `test_behavioral_core_is_cic_at_full_weight`
- [ ] `test_tax_discipline_absent_from_rollup`
- [ ] `test_bonus_factors_contribute_one_twentieth`
- [ ] `test_none_bonus_contributes_zero`
- [ ] `test_final_grade_weights_are_40_25_25_10`

### Precision

- [ ] `test_final_grade_is_not_rounded` — first golden row grades `70.98376463`, not `71`
- [ ] `test_interest_rate_derives_from_unrounded_grade` — the same row prices at `14.32129883`,
      and using a grade of `71.0` would give `14.32`, which must fail
- [ ] `test_money_fields_are_decimal_not_float`

### Pricing and repayment

- [ ] `test_target_payment_worked_example` — loan 3,000,000,000, term 3, grade 70.98376463,
      bank rate 12.0 → target payment ≈ 3,107,409,741 (requirements §6, SME-0001)
- [ ] `test_daily_repayment_rate_uses_21_and_252_day_conventions`
- [ ] `test_bank_rate_at_or_above_20_raises`
- [ ] `test_rate_never_exceeds_20_percent_cap`

### Gates and decision

- [ ] `test_hard_gate_produces_reject`
- [ ] `test_soft_gate_produces_review`
- [ ] `test_no_gate_produces_approved`
- [ ] `test_hard_gate_beats_soft_gate`
- [ ] `test_gate_3_disabled_by_default_and_config_switchable`
- [ ] `test_gate_7_disabled_by_default_and_config_switchable`
- [ ] `test_gate_2_uses_term_over_operating_history_not_inverse`
- [ ] `test_excluded_industry_rejects`
- [ ] `test_fraud_flag_rejects`
- [ ] `test_fired_gates_are_reported_with_ids`

### States

- [ ] `test_insufficient_data_when_fewer_than_24_months`
- [ ] `test_insufficient_data_when_revenue_zero`
- [ ] `test_insufficient_data_is_not_a_low_score` — asserts `factor_scores` are `None`, not 0
- [ ] `test_ai_pending_when_ai_score_missing`
- [ ] `test_ai_pending_still_returns_deterministic_premiums`
- [ ] `test_profit_not_positive_raises`

### Purity — the guard rails against the one rule

- [ ] `test_grade_is_deterministic_across_repeated_calls` — same input, 100 calls, identical output
- [ ] `test_grading_package_imports_nothing_from_app` — walk the package AST; assert no `app.*` import
- [ ] `test_grading_package_has_no_async_def` — AST walk; no coroutines in the core
- [ ] `test_grade_performs_no_io` — monkeypatch `open`, `socket.socket` and `datetime.now` to raise;
      `grade()` still succeeds
- [ ] `test_grade_does_not_mutate_input` — input object unchanged after the call

---

## 9. Open Questions

**None of these block implementation, and this spec may proceed to ACCEPTED with them open.**

`_TEMPLATE.md` normally requires all open questions closed before ACCEPTED. That rule is right for
design ambiguity and wrong here: every item below is either config-switchable or raises loudly rather
than guessing, so none can produce a silently wrong grade. Holding the spec at REVIEW until the CEO
answers all seven would stall the first end-to-end lending flow for no engineering benefit.

These items are tracked to resolution in **`docs/specs/underwriting/grading-engine-deviations.md`**
(items D19–D27), which is a living register rather than a spec gate. **Resolution target: after the
first end-to-end flow is demonstrable.** Approved by Edward, 28 July 2026.

The deviations register also records 13 places where requirements v0.2 is factually wrong and this
implementation is correct (D1–D13), and 5 deliberate departures from the doc or from `CLAUDE.md`
(D14–D18). Read it before changing any constant in this spec.

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | **Gate 3 threshold.** At "≥3 factors below 50" the gate fires on 98.4% of the golden set; at "≥4", 95.2%. The median SME has 8 of 22 below 50. Needs to be a proportion, or restricted to crucial (non-bonus) factors, or a much higher count. Ships disabled. | Loc | — |
| 2 | **CIC scale.** Requirements cite both 0–700 and 150–750; the workbook's generator says 150–750 and the observed range is 442–750, but the reference band table anchors up to 800. Gate 7 is a final reject at ≤500, so it ships disabled. | Loc | — |
| 3 | **`profit ≤ 0`.** The workbook has no rule. On the SCSR curve a negative ratio scores ≈100, so a loss-making SME would be *rewarded*. Core raises `ValueError` for now. Options: score 0, or route to `REVIEW`. | Loc / Edward | — |
| 4 | **`risk_grade` letter vs number.** `ScoreRun.risk_grade` is `Text` and the mock writes `"B"`, but the requirements are explicit that the output is "0–100 nominal, no letter grades". Spec 2 needs a decision: drop the column, or derive bands from the grade. | Edward | — |
| 5 | **`owner_withdrawal` input scale.** The YAML defines a cubic over a 0–1 ratio, but the golden set supplies this factor as an already-computed 0–100 score, so the cubic is unexercised by the fixture. Confirm which the production input will be. | Loc | — |
| 6 | **AI rubrics** for the six sector factors and Founder Experience. Not blocking — they are inputs (R3), and their absence yields `AI_PENDING`. | Loc | — |
| 7 | **Sector fallback at launch.** Six of seven sector factors are AI-graded, so 86% of a group worth 25% of the grade is unavailable until rubrics land. Options: a static per-industry table, or reweight pre-launch. | Loc / Edward | — |

---

## Appendix — Provenance

The parameters in `grading_params_v1.yaml` were extracted from
`FundLok formula factors v0.xlsx`, tab `Scoring From Raw`, production columns AI–BO, and verified by
recomputing all 22 factor scores, 4 premiums and the final grade for all 10,000 rows in Python. Every
value matched to a relative tolerance of 1e-7.

Three tabs in that workbook are **not** authoritative and should be ignored:

- `Cashflow` — holds abandoned earlier curve fits for factors 5 and 6 that do not match their own
  band tables.
- `1st version of calculation` — superseded.
- The pricing columns of `Scoring From Raw` (BP–BT) — computed against a stale, different dataset
  than the grade columns.

Requirements v0.2 disagrees with the workbook on: the curve form (§3.2), the RSG seasonality weight
(§3.4), the Behavioral core composition (§3.4), the Top 3 concentration curve (§3.2), factors 5 and
6 parameters (§3.2), the CIC scoring method (§3.2), the Owner Withdrawal method (§3.2), and the Gate
3 threshold (§3.5). Where they differ, the workbook wins. A separate note back to Loc should get the
requirements doc corrected so it stops being a trap for the next reader.

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Edward | Initial draft. Params and golden-set fixture committed alongside. |
