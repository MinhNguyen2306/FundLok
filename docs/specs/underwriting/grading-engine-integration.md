# Spec: Grading Engine — Integration

| Field | Value |
|---|---|
| **Status** | DRAFT |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/underwriting/` |
| **Version** | 0.1 |
| **Date** | 2026-07-28 |
| **Related ADR** | — |
| **Depends on** | `docs/specs/underwriting/grading-engine-core.md` — must be ACCEPTED and merged first |

> **This spec is a scope boundary, not yet an implementable plan.** It exists so spec 1 has a clear
> edge and so the work it defers is written down rather than remembered. Do not hand this to an
> implementer. Promote it to REVIEW once spec 1 is merged and Open Questions 1–4 there are resolved.

---

## 1. Context & Goal

Spec 1 delivers a pure grading core: `grade(inputs, params) → GradingResult`, with no I/O and no
knowledge of FundLok. This spec wires it into the platform — replacing the mock in
`app/underwriting/service.py::start_score_run`, persisting results so any past decision can be
reconstructed, and routing the outcome to the marketplace or the review queue.

**Goal:** a real score run — application in, persisted and auditable grade out, correctly routed.

---

## 2. Out of Scope

- Everything in spec 1 (all calculation).
- Document ingest and parsing (VAT declarations, Form B02-DN, CIC report). Until parsers exist, the
  fields spec 1 needs arrive from the application form and admin entry. **This is the largest
  remaining gap between here and production** and needs its own spec.
- The AI scoring service for the seven graded factors (separate spec; rubrics outstanding).
- The investor pros/cons summary generator (separate spec).
- Frontend. Phat owns any UI for the review queue.

---

## 3. Data Model — open design questions

`score_runs` already exists (`app/lending/models.py:149`) with `overall_score Numeric(5,2)`,
`risk_grade Text`, `recommended_terms JSONB`, `factor_results JSONB`, `locked_at`.

Decisions needed before this spec can be written properly:

1. **Precision.** `Numeric(5,2)` truncates the grade to two decimals, but the interest rate must
   derive from the unrounded value (spec 1 R5). Either widen the column via migration, or persist the
   full-precision grade and rate inside `factor_results` and treat `overall_score` as display-only.
   The rate must be **stored**, never recomputed from the truncated column.
2. **Replay fields.** Reconstructing a decision needs `engine_version`, `params_version`, and the
   normalised input snapshot stored per run. None of those columns exist. Probably a new
   `score_run_inputs` table (append-only, consistent with the ledger pattern) rather than more JSONB.
3. **`risk_grade`.** Currently `Text`, mock writes `"B"`, requirements say 0–100 with no letter
   grades. Drop it, or define bands. (Spec 1, Q4.)
4. **Raw document provenance.** Replaying "you misread my VAT form" needs the source documents linked
   to the run, not just the parsed numbers. Depends on the ingest spec.
5. **New states.** `INSUFFICIENT_DATA` and `AI_PENDING` must map onto `ScoreRun.status`, which is
   currently `RUNNING → READY → LOCKED`. Extending that enum is a shared-model change and needs
   Phat's agreement per `CLAUDE.md`.

---

## 4. API Contract

`POST /underwriting/score-runs` and `POST /underwriting/score-runs/{id}/approve` already exist and
are ADMIN-only. The response models gain the real grade, the four premiums, the price, the repayment
schedule, the fired gates and the decision. Exact shape to be agreed with Phat before implementation,
per the spec-driven workflow.

---

## 5. State Machine

```
ScoreRun:  RUNNING ──► READY ──► LOCKED
                   └──► ??? (INSUFFICIENT_DATA, AI_PENDING)
```

Resolving the `???` branch is item 5 in §3.

---

## 6. Business Rules — sketch

1. `start_score_run` calls `grade()` synchronously inside the async service. The core is sync by
   design (spec 1 R1); the service owns the async boundary and the DB.
2. Every run persists `engine_version` + `params_version` + input snapshot. A run that cannot be
   replayed is a bug.
3. `APPROVED` → publish to marketplace. `REVIEW` → review queue with the fired gates and their
   evidence requirements. `REJECT` → terminal, SME notified. Hard rejects are not overridable.
4. Manual review decisions are captured with actor, timestamp, rationale and any override, via
   `app/utils/audit.py`. Already the pattern in `router.py`.
5. Scoring must be idempotent per application + params_version, so a retry cannot produce a second
   divergent grade for the same inputs.
6. Long-running work belongs in ARQ, not `BackgroundTasks` (`CLAUDE.md`). The core itself is fast —
   pure arithmetic over 24 numbers — so a synchronous call is likely fine; the AI factor calls are
   what will need the worker.

---

## 7. Error Cases

To be written. At minimum: what the endpoint returns for each of the five decision states, and what
happens when `grade()` raises (`profit ≤ 0`, out-of-range loan, unsupported industry, bank rate ≥ 20).

---

## 8. Acceptance Criteria

To be written once §3 is resolved. Will include, at minimum:

- [ ] `test_score_run_persists_full_precision_grade_and_rate`
- [ ] `test_score_run_records_engine_and_params_version`
- [ ] `test_score_run_is_replayable_from_stored_inputs` — re-running a stored snapshot under the same
      `params_version` reproduces the original grade exactly
- [ ] `test_insufficient_data_does_not_produce_a_score_run_with_a_low_grade`
- [ ] `test_approved_run_publishes_to_marketplace`
- [ ] `test_review_run_enters_queue_with_fired_gates`
- [ ] `test_hard_reject_cannot_be_overridden`
- [ ] `test_duplicate_score_run_for_same_application_and_params_is_idempotent`
- [ ] `test_score_run_requires_admin_role`

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Widen `overall_score`, or keep full precision in JSONB only? | Edward | — |
| 2 | New `score_run_inputs` table, or extend `score_runs`? | Edward | — |
| 3 | Extend `ScoreRun.status` with the two new states — needs Phat's sign-off (shared model) | Edward / Phat | — |
| 4 | Drop `risk_grade` or define bands? | Edward | — |
| 5 | Where do `operating_months` and the KYC/AML result enter the pipeline? `app/verification/` presumably owns the latter | Edward | — |
| 6 | Does scoring run inline or via ARQ once AI factor calls are added? | Edward | — |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-07-28 | Edward | Scope boundary for spec 1. Not implementable yet. |
