# PR: Grading engine — deterministic core

**Branch:** `feature/underwriting/grading-core` (off `main` @ `18be162`)
**Spec:** [docs/specs/underwriting/grading-engine-core.md](../specs/underwriting/grading-engine-core.md) (ACCEPTED v1.0)
**Deviations register:** [docs/specs/underwriting/grading-engine-deviations.md](../specs/underwriting/grading-engine-deviations.md)

## What this does

Implements spec 1 exactly: a new `app/underwriting/grading/` package that takes an
already-normalised loan application and produces 22 factor scores → 4 group premiums →
a full-precision final grade → an interest rate and repayment schedule → a knockout-gate
decision. `types.py` holds the frozen `GradingInput`/`GradingResult`/`GateResult`
dataclasses; `params.py` loads `grading_params_v1.yaml` into a frozen, recursively
immutable `ParamSet` (mutating any level raises); `curves.py` implements the sigmoid /
linear / cubic primitives from R2 (`intercept` is not a midpoint — true midpoint is
`intercept/steepness`); `derive.py` computes the 11+ derived metrics from R6 (population
stdev, the ten-overlapping-3-month-window trend, "avg monthly × term" rather than
trailing-N-months, COGS kept separate from variable cost); `factors.py` scores all 22
factors, dispatching on `kind` from the YAML; `rollup.py` builds the 4 premiums (RSG's
seasonality at ¼ not ⅓, CIC at full weight in Behavioral, bonus factors at `score/20`,
no clamping — asserts instead) and the final grade; `pricing.py` and `gates.py` implement
R10 and R9 (gates 3 and 7 read `enabled` off the YAML, so either is switchable by a
config change alone); `engine.py`'s `grade()` is the single orchestrating entry point.

The whole package is a pure library per R1: no imports from `app/`, no I/O except
`load_params()` reading the YAML once, every function plain `def` (no `async def`) —
this is a deliberate, spec-approved departure from `CLAUDE.md`'s async convention
(deviations register D14), enforced by an AST-walking test rather than just a comment.

`app/underwriting/service.py`, `router.py`, `schemas.py`, `app/lending/models.py` and the
Alembic chain are untouched — wiring `grade()` into `start_score_run()` and persisting
`GradingResult` is spec 2 (`grading-engine-integration.md`, still DRAFT), not this PR.

All 60 spec §8 acceptance criteria are implemented as `tests/underwriting/` pytest tests
(50 test functions — some bullets share a test where that reads more naturally, e.g. the
YAML-drift and version-pin checks live together) — **50 passed, 0 failed**, including
`test_golden_set_full_reconciles_all_10000_rows`: every one of the 10,000 fixture rows
reconciles all 22 factor scores, all 4 premiums, and the final grade within the spec's
tolerance (`abs(actual-expected) <= max(1e-6, abs(expected)*1e-7)`) — 270,000+ assertions,
zero failures, no changes to the fixture or the YAML.

## Judgment calls worth a second look

**1. Owner Withdrawal input (D22, already flagged open in the deviations register).**
The YAML models factor 21 as a cubic over a 0–1 raw ratio, but the golden set supplies it
as an already-computed 0–100 score — confirmed exactly: `expect_owner_withdrawal ==
owner_withdrawal_raw` for every reconciled row, with no cubic transform in between.
`factors.py` special-cases this factor to pass the supplied value straight through
(clamped-by-assertion, not silently re-clamped) rather than running it through
`curves.cubic`. The cubic itself is implemented and tested directly
(`test_cubic_owner_withdrawal_matches_band_anchors`, band anchors x=0.2→≈99, x=1.0→0) so
it's ready the moment the raw ratio becomes the real production input — this is an
interim behaviour per D22, not a permanent design decision, and D22 is still open in the
register with Loc as owner.

**2. Industry validation vs. the excluded-industry gate.** `supported_industries` (15
sectors with scoring data) and `excluded_industries` (gambling, alcohol, tobacco,
weapons, defence) are disjoint lists in the YAML. If input validation only accepted
`supported_industries`, gate 5 (`excluded_industry`, hard) could never fire — every
excluded application would raise `ValueError` before grading even started, never reaching
the gate that's supposed to reject it. `engine._validate_inputs` accepts an industry in
*either* list (only an industry in neither is treated as a genuine input error/typo), so
an excluded-industry application grades normally and then gets hard-rejected by gate 5 —
the same pattern gate 6 (`kyc_aml`) already uses. Not explicitly called out in the spec;
inferred from gate 5's existence implying excluded industries must be a reachable input.

**3. AI_PENDING vs. a hard gate firing simultaneously.** The spec doesn't state a
precedence when an AI score is missing *and* a hard gate (e.g. failed KYC) also fires.
`engine.grade()` resolves hard-gate REJECT before AI_PENDING before soft-gate REVIEW — a
KYC/fraud/excluded-industry failure is an absolute block that shouldn't be masked by
"still waiting on AI," while AI_PENDING in turn supersedes an ordinary soft-gate REVIEW.
Not tested as a combined scenario since the spec's acceptance criteria test each state
independently; flagging the ordering choice in case it should be explicit in spec 2.

**4. Sector group renormalization under AI_PENDING.** R8 says a group with a missing AI
factor is "computed over the factors present." For `sector` (mean of 7, all core, no
bonus) I read that as a proper renormalized average over the factors that are present,
not the weighted sum left to silently shrink by the missing factor's weight — implemented
in `rollup.compute_group_premium`. Golden set rows never hit this path (all AI scores are
always present in the fixture), so it's unverified against the workbook; only exercised
by hand-built tests (`test_ai_pending_still_returns_deterministic_premiums`).

## Files

- `app/underwriting/grading/` — new package: `types.py`, `params.py`, `curves.py`,
  `derive.py`, `factors.py`, `rollup.py`, `pricing.py`, `gates.py`, `engine.py`,
  `__init__.py`. (`params/grading_params_v1.yaml` pre-existed, untouched.)
- `tests/underwriting/` — new: `conftest.py` + `test_params.py`, `test_curves.py`,
  `test_derivations.py`, `test_rollup.py`, `test_precision.py`, `test_pricing.py`,
  `test_gates.py`, `test_states.py`, `test_purity.py`, `test_golden_set.py`.
  (`fixtures/golden_set.csv.gz`, `fixtures/golden_set_sample.csv` pre-existed, untouched.)
- `requirements.txt` — added `pyyaml` (not previously declared; the params loader needs
  it). The only file touched outside the two directories above.

## Verification

- `pytest tests/underwriting` (run with `--confcutdir=tests/underwriting` in the sandbox
  this was built in, which lacks a live Postgres/`httpx` for the repo's root
  `conftest.py` — not needed in your normal dev environment per ADR-005, where
  `docker compose up -d postgres` is already running and `requirements.txt` is fully
  installed): **50 passed, 0 failed.**
- `test_golden_set_full_reconciles_all_10000_rows` specifically: 10,000/10,000 rows,
  all factor/premium/final-grade values within tolerance.
- Manually spot-checked the spec's worked example (SME-0001: grade 70.98376463 → rate
  14.32129883% → target payment ≈3,107,409,741 on a 3bn/3-month loan) and several
  hand-built edge cases (profit ≤ 0 raises, insufficient data short-circuits without a
  divide-by-zero, AI_PENDING still returns premiums, hard gate beats soft gate, gates 3/7
  flip on via a modified YAML with no code change).
