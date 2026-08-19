# PR — docs(underwriting): correct the BA grading guide, add the AI_PENDING path

| Field | Value |
|---|---|
| **Branch** | `docs/underwriting-grading-guide-ai-pending` |
| **Type** | Documentation + test harness. **No production code touched.** |
| **Module** | `app/underwriting/` (docs), repo-root BA harness |
| **Spec** | `docs/specs/underwriting/grading-engine-core.md` (ACCEPTED v1.0) — R3, R8, R9 |
| **Migration** | None |
| **Risk** | None to runtime. `app/` is unmodified. |

---

## Why

`GRADING_TEST_CASES_GUIDE.md` is the document a BA, PO or frontend engineer reads to understand
what the grading engine decides. It disagreed with the engine in five places. Phat hit the first
one while scoping the frontend integration, which is how this was found.

Nothing here changes behaviour — it makes the documentation match `app/underwriting/grading/`.

---

## What was wrong

| # | Claim in the guide | Reality in the code | Consequence |
|---|---|---|---|
| 1 | Four decision states | Five — `AI_PENDING` exists (`types.py:25`, `engine.py:128-135`) | A frontend built from this guide has no state to render for the most common outcome pre-AI-service. |
| 2 | `APPROVED` = 80–100, `REVIEW` = 70–79.99, `REJECT` = <70 | **No score bands exist.** The decision is entirely gate-driven; the grade only sets the rate. | Materially misleading. Golden-set grades run 46.19–86.53, median 68.60, so this table implies we reject nearly every applicant. |
| 3 | Gate 7 (`cic_floor`) listed as active; Gates 3 and 4 absent | Gates 3 and 7 ship `enabled: false`; Gate 4 is UI-enforced | A BA writing a "CIC 450 must reject" case gets `APPROVED` and files a bug against correct behaviour. |
| 4 | `industry` allowed values: `IT Services, Retail Trade, Manufacturing, Logistics, Healthcare` | 15 exact strings in `supported_industries`. `Logistics` and `Healthcare` are **not** among them (`Logistics & Transport`, `Healthcare & Pharmacy`) | An unsupported industry raises `ValueError` — the harness crashes rather than grading. |
| 5 | `INSUFFICIENT_DATA` = missing months or missing CIC | Also fires on blank `kyc_aml_passed`, or zero Y1 revenue / total cost / min trailing-12 (`engine.py:78-88`) | Incomplete. |

## What changed

**`GRADING_TEST_CASES_GUIDE.md`**

- Cheat sheet rewritten: five states, gate-driven triggers, score-band column removed with an
  explicit note that it never existed (so nobody re-adds it from an old copy).
- Added the resolution order — `REJECT → AI_PENDING → REVIEW → APPROVED`, with
  `INSUFFICIENT_DATA` short-circuiting ahead of all of them — and why hard gates outrank
  `AI_PENDING`.
- Gates table gains Gates 3 and 4 and a **Status** column marking 3 and 7 disabled, with the
  reason each ships off. Clarified that `cic_score` is still required even though its floor is off.
- Added the 15 supported industries verbatim, plus the 5 excluded ones as reject-path fixtures.
- Added a section on the seven `ai_*` columns: they are inputs, the engine never calls an AI
  service, and a blank one yields `AI_PENDING`.
- **Documented that an `AI_PENDING` run still returns a grade and rate, and that both are
  provisional and biased low** — Sector renormalises over present factors, but `founder` is a
  bonus factor, so a missing founder score contributes 0 rather than being renormalised away.
- Fixed the template link, which pointed at `file:///Users/huynhphat/Downloads/...` and resolved
  for nobody.

**`grading_demo.py`**

- A blank `ai_*` column is now omitted from `ai_scores` instead of being passed to `float("")`.
  Previously the guide's own instruction to leave a cell blank crashed the harness with a
  `ValueError`, so the `AI_PENDING` branch was unreachable from the BA workflow.
- `AI_PENDING` gets a display branch, and grade/rate are labelled `PROVISIONAL — do not quote`
  under it.

**`grading_test_cases.csv`**

- Added `Case 5` — Case 1 with `ai_founder` blank — so all five decision states are exercised by
  the default template.

---

## Verification

`python3 grading_demo.py` — five cases, five distinct decisions, all matching `expected_decision`:

| Case | Decision | Grade | Rate |
|---|---|---|---|
| 1 | `APPROVED` | 92.45 | 11.22% |
| 2 | `REVIEW` (soft gate 8) | 78.50 | 12.54% |
| 3 | `REJECT` (hard gate 6) | 64.88 | 14.81% |
| 4 | `INSUFFICIENT_DATA` | N/A | N/A |
| 5 | `AI_PENDING` | 91.98 *(provisional)* | 11.26% *(provisional)* |

Cases 1 and 5 are the same applicant apart from one missing AI score, and the gap — 92.45 → 91.98,
11.22% → 11.26% — is the low-bias effect now documented in the guide.

`app/` is untouched, so the engine test suite including the 10,000-row golden set is unaffected;
CI is the check.

---

## Follow-ups this surfaces (not in this PR)

1. **`AI_PENDING` must not expose a provisional rate through the API.** Spec 2
   (`grading-engine-integration.md`) should state that grade and rate are withheld from any
   response whose decision is `AI_PENDING`, rather than leaving it to each caller. This is a
   mispricing risk, not a presentation detail.
2. **Open Question 3 in spec 2** — mapping `INSUFFICIENT_DATA` and `AI_PENDING` onto
   `ScoreRun.status` — needs Phat's sign-off before the integration work starts.
3. The score-band table in item 2 above came from somewhere. Worth checking whether the CEO's
   requirements assume approval thresholds that the engine does not implement.
