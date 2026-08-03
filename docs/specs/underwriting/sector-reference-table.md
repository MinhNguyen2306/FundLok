# Spec: Sector Reference Table

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) — delegable to an implementing model |
| **Module** | `app/underwriting/grading/` |
| **Version** | 1.0 |
| **Date** | 2026-07-28 |
| **Related ADR** | — |
| **Depends on** | `grading-engine-core.md` (ACCEPTED, merged) |
| **Related** | `grading-engine-deviations.md` (D22, D26, D27, D28), `grading-engine-calibration.md` §2.5 |

---

## 1. Context & Goal

Seven of the 22 grading factors cannot be computed from an SME's own financials. Six are the
AI-graded Sector factors (14–19); the seventh is Founder Experience (22). Additionally, factor 13
(Sector Growth Rate) needs an industry CAGR that requirements §2.4 always specified as a config table
and which was never supplied.

Today the engine takes all of these as per-application inputs, which means **no real application can
be scored** — there is nothing to populate them from, so every application returns `AI_PENDING`.

The CEO's intent was an LLM assessing sector risk per application. That is deferred in favour of a
versioned lookup table, for two reasons. Sector risk is *systematic* — every F&B borrower faces the
same regulatory and cyclical exposure — so an industry-level number is the correct model rather than a
compromise. And it is explainable: "Construction Materials scores 25 on cyclicality, table v1" is
defensible to a borrower or the SBV in a way an inline LLM judgment is not. AI is still used, but to
*author* the table offline with human review, not at scoring time.

**Goal:** supply the seven per-industry values plus the Founder constant from a versioned, replayable
reference file, so that a complete application can be scored end to end.

---

## 2. Out of Scope

- **Any change to `grade()` or the scoring maths.** See §6 R2 — this is the single most important
  constraint in this spec.
- Per-application LLM sector scoring. That is the v2 upgrade path (§6 R6), unblocked by this design.
- Document ingest and parsing (VAT, B02-DN, CIC). Separate future spec.
- Persistence, endpoints, review queue — `grading-engine-integration.md`, still DRAFT.
- Populating the table's *content*. Already done: `sector_reference_v1.yaml` ships with all 105 values
  drafted and flagged `DRAFT_UNREVIEWED`. This spec covers the mechanism only.

---

## 3. Data Model

**No database changes. No tables. No migrations.**

### Files already committed (do not edit as part of implementation)

```
app/underwriting/grading/params/
├── grading_params_v1.yaml         # existing, unchanged
├── sector_reference_v1.yaml       # NEW — 15 industries x 7 columns + constants
└── sector_reference_prompt.md     # NEW — authoring prompt, for refreshes
```

### New module

```
app/underwriting/grading/
└── sector_reference.py            # loader + resolver
```

### Reference file shape (already written)

```
sector_reference_version   str        pinned by callers for replay
status                     str        DRAFT_UNREVIEWED | REVIEWED
review                     {reviewed_by, reviewed_at}
calibration                {…}        constraints the content was built to
columns                    mapping    per-column provenance and validation
  <column>
    ├── factor_id          int
    ├── kind               "score" | "raw_percent"
    ├── valid_range        [min, max]
    ├── source, as_of, cadence, reviewed_by
industries                 mapping    15 entries, 7 values each
constants                  {founder: int}
notes                      list[str]
```

**Two kinds of column, and they are not interchangeable:**

- Six columns are `kind: score` — finished 0–100 factor scores, used as-is.
- `cagr_pct` is `kind: raw_percent` — a raw percentage fed to factor 13's sigmoid. **It may be
  negative.** Validating it as 0–100 is a bug.

---

## 4. API Contract

No HTTP endpoint. Two functions added to the package's public surface:

```python
from app.underwriting.grading import load_sector_reference, resolve_sector_inputs

ref = load_sector_reference()                       # or load_sector_reference(path=...)
resolved = resolve_sector_inputs("Logistics & Transport", ref)
```

`resolve_sector_inputs` returns a frozen mapping:

```python
{
    "ai_scores": {          # 6 sector factors + founder constant, all 0-100
        "regulatory": 55.0,
        "input_cost_vol": 30.0,
        "cyclicality": 45.0,
        "competitor": 40.0,
        "macro": 38.0,
        "uncontrollable": 45.0,
        "founder": 50.0,
    },
    "sector_cagr_pct": 10.5,                        # raw percent, NOT a score
    "sector_reference_version": "v1-20260728",
    "provisional": True,                            # True while status is DRAFT_UNREVIEWED
}
```

Callers merge `ai_scores` into `GradingInput.ai_scores` and `sector_cagr_pct` into
`GradingInput.sector_cagr_pct`. The engine is unchanged and unaware this file exists.

Both functions are synchronous `def`, consistent with the core (D14).

---

## 5. State Machine

None. This spec introduces no status field. The reference file has a `status`
(`DRAFT_UNREVIEWED` → `REVIEWED`) which is data, not application state.

---

## 6. Business Rules

### R1 — AI authors this file offline. The engine never calls an LLM.

`sector_reference_prompt.md` is run by an engineer, reviewed by a human, signed off by the CEO, and
the result is committed and versioned. Nothing in `app/` may call an AI service to populate these
values at request time. The whole point is that a past grade can be reconstructed by loading a
versioned file.

### R2 — DO NOT wire this into `grade()`. This will break 10,000 regression rows.

**The golden-set fixture supplies its own per-row sector values and CAGR.** They are not
industry-level, and they will not match this table.

If `resolve_sector_inputs` is called inside the scoring path — or if `grade()` is changed to look up
sector values by industry — then `test_golden_set_full_reconciles_all_10000_rows` fails and you have
destroyed the regression guard that makes this module safe to change.

The resolver is an **alternative input source for production callers assembling a `GradingInput`**. It
sits beside the engine, not inside it. `grade()`, `engine.py`, `factors.py` and `rollup.py` must not
be modified by this spec at all.

If the golden test fails after your changes, that is the diagnosis.

### R3 — Never retype a value. Load it.

Same rule as the core params (grading-engine-core.md R2). No sector score, CAGR figure or the founder
constant may appear as a Python literal. They live in YAML and are read.

### R4 — Validate per column `kind`, not uniformly.

- `kind: score` → must be within `valid_range` `[0, 100]`
- `kind: raw_percent` → must be within its own `valid_range`, which permits negatives

On load, validate that all 15 industries are present, that each has all 7 columns, that every value
is in its column's range, and that the industry names match `supported_industries` in
`grading_params_v1.yaml` exactly. Fail loudly at load time, not at scoring time.

### R5 — Unreviewed data is surfaced, never silently trusted.

While `status: DRAFT_UNREVIEWED`, `resolve_sector_inputs` sets `provisional: True`. Callers are
expected to propagate that so a result can be marked as not-yet-CEO-approved. This spec does not
define what consumers do with it — that is spec 2 — but the flag must be present and accurate.

### R6 — The upgrade path must stay open.

Because the six sector factors are `kind: supplied` in `grading_params_v1.yaml`, swapping a table
lookup for a per-application LLM score is a change of *source*, per factor, with no engine change.
Do not design anything that assumes the table is the only possible source. A future
`resolve_sector_inputs` may take an override mapping for factors already served by an AI service.

### R7 — Refresh is per column, and provenance travels with it.

The natural update unit is a column — one factor across all 15 industries — because that is how source
data arrives (SBV quarterly for macro, GSO annually for CAGR). Event-driven regulatory changes may
alter a single cell. Any value change requires: update the cell, update that column's `as_of`, reset
that column's `reviewed_by` to null, bump `sector_reference_version`, and **keep the previous file**
rather than overwriting it. Historical score runs pin a version and must stay loadable.

### R8 — Calibration constraints are load-bearing.

The `calibration` block records that this draft averages a Sector premium of 53.56 against today's
observed 54.75 — a ~2bp move across the book. Sector drives **36% of the interest rate spread**
(grading-engine-calibration.md §2.5), so a table that averages 65 instead of 55 cuts roughly 21bp off
every loan. A check script must verify the achieved mean and range after any edit.

### R9 — Founder Experience is a constant here, not a factor change.

CEO-approved (28 Jul 2026). The value is 50, which is the observed median in the golden set, so it is
pricing-neutral. **Factor 22 and its `/20` weight in the Behavioral roll-up stay exactly as they are** —
removing the factor would invalidate the golden set's `expect_behavioral` and `expect_final_grade`
columns. We supply a constant, we do not change the model.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Industry not in the table | `raise KeyError` naming the industry and listing valid ones | exception |
| Industry name differs in case or spacing from `supported_industries` | Load-time validation failure — names must match exactly | exception at load |
| A `score` column outside 0–100 | Load-time validation failure | exception at load |
| `cagr_pct` outside its `valid_range` | Load-time validation failure | exception at load |
| Missing column for an industry | Load-time validation failure naming industry and column | exception at load |
| Fewer or more than 15 industries | Load-time validation failure | exception at load |
| YAML file absent | `FileNotFoundError` with the expected path | exception |
| `status: DRAFT_UNREVIEWED` | Resolve normally, set `provisional: True` | normal result, flagged |
| Caller mutates the returned mapping | Returned structure is frozen; mutation raises | exception |

---

## 8. Acceptance Criteria

Under `tests/underwriting/`. These become pytest function names.

### The one that must not break

- [ ] `test_golden_set_still_reconciles_after_sector_reference_added` — the existing
      `test_golden_set_full_reconciles_all_10000_rows` still passes, unchanged, over all 10,000 rows.
      **If this fails, R2 was violated.**
- [ ] `test_grade_signature_and_behaviour_unchanged` — `grade()` produces identical output for a fixed
      input before and after this change

### Loading and validation

- [ ] `test_sector_reference_loads_and_is_frozen`
- [ ] `test_sector_reference_version_pinned` — version is `"v1-20260728"`
- [ ] `test_all_15_industries_present`
- [ ] `test_industry_names_match_supported_industries_exactly`
- [ ] `test_every_industry_has_all_seven_columns`
- [ ] `test_score_columns_validated_0_to_100`
- [ ] `test_cagr_column_permits_negative_values` — asserts `cagr_pct` is *not* validated as 0–100
- [ ] `test_missing_column_fails_at_load_not_at_scoring`
- [ ] `test_out_of_range_score_fails_at_load`
- [ ] `test_wrong_industry_count_fails_at_load`

### Resolution

- [ ] `test_resolve_returns_six_sector_scores_plus_founder`
- [ ] `test_resolve_returns_cagr_separately_from_ai_scores` — CAGR must not appear in `ai_scores`
- [ ] `test_resolve_unknown_industry_raises_with_valid_options`
- [ ] `test_resolve_includes_reference_version`
- [ ] `test_resolve_marks_provisional_while_status_is_draft`
- [ ] `test_resolved_mapping_is_immutable`
- [ ] `test_founder_constant_is_50`
- [ ] `test_no_sector_value_appears_as_python_literal` — AST walk over `sector_reference.py`; no
      numeric literal matching a table value

### End to end, using the resolver

- [ ] `test_application_with_resolved_sector_inputs_reaches_a_decision` — a `GradingInput` assembled
      using `resolve_sector_inputs` produces a decision other than `AI_PENDING`. **This is the
      user-visible point of the whole spec.**
- [ ] `test_two_industries_produce_different_sector_premiums`
- [ ] `test_logistics_scores_lower_on_input_cost_than_professional_services` — fuel versus salaries

### Calibration guard

- [ ] `test_achieved_mean_sector_premium_within_tolerance_of_calibration_block` — computed mean across
      the 15 industries matches `calibration.achieved_mean_premium` (53.56) within 0.5
- [ ] `test_premium_range_matches_calibration_block` — roughly 38.9 to 72.0
- [ ] `test_sector_premium_spread_exceeds_25_points` — guards against a future refresh flattening the
      table and silently removing sector differentiation

---

## 9. Open Questions

Non-blocking. Tracked in `grading-engine-deviations.md`.

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | CEO review of all 105 drafted values. Until then `status: DRAFT_UNREVIEWED`. | Loc | — |
| 2 | Confirm data sources: GSO for CAGR, SBV for the macro column. Currently marked TO BE CONFIRMED. | Loc | — |
| 3 | Per-column refresh cadences are drafted (quarterly macro, annual CAGR, event-driven regulatory). Confirm against actual Vietnamese release schedules. | Loc / Edward | — |
| 4 | When rubrics exist, which factors move first from table to per-application LLM? R6 keeps this open. | Loc | — |
| 5 | Should `provisional: True` block publication to the marketplace, or only annotate it? | Edward | spec 2 |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-28 | Edward | Initial. Reference file and authoring prompt committed alongside. |
