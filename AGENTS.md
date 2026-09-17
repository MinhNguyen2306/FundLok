# AGENTS.md

Guidance for AI coding agents (Claude Code, Cursor, Copilot, Gemini, etc.) working in this repository. It maps the [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) skill set to FundLok workflows.

## Repository Overview

FundLok MVP Backend — the API backend for the FundLok fintech platform.

- **Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic v2, Uvicorn
- **App code:** `app/` (domain modules: `auth`, `users`, `admin`, `sme`, `lending`, `loans`, `underwriting`, `contracts`, `market`, `payments`, `projects`, `files`, `system`, `core`, `models`, `schemas`)
- **Migrations:** `alembic/`
- **Tests:** `tests/` (pytest; run with `pytest`)
- **Docs:** Swagger UI at `/docs`

Because this is a **fintech** backend, correctness, security, and auditability outweigh speed. Prefer the verification-heavy skills (`doubt-driven-development`, `security-and-hardening`, `test-driven-development`) by default.

## How Skills Are Installed

This repo vendors the agent-skills collection under `.claude/`:

```
.claude/skills/<name>/SKILL.md   → 24 engineering skills + `fundlok-domain` (auto-discovered by Claude Code)
.claude/agents/<role>.md          → reusable subagent personas
.claude/commands/<name>.md        → slash commands (/spec, /plan, /build, /test, /review, /code-simplify, /ship, /webperf)
references/<topic>-checklist.md    → checklists referenced by skills
```

Claude Code auto-discovers skills in `.claude/skills/` and subagents in `.claude/agents/`. Other agents (Cursor, Copilot, Gemini) should read the `SKILL.md` files directly and follow them.

## Domain Rules (read before touching money)

Before writing or changing code that touches **money, rates, grading,
schedules, repayment, relief, extension, backstop, fees, the ledger,
disbursement, revenue evidence, investor disclosure, eligibility or audit** —
and before naming anything user-facing — consult the **`fundlok-domain`** skill
(`.claude/skills/fundlok-domain/SKILL.md`). It encodes the FundLok Handbook v3
as engineering invariants. These are not open for discussion; check there
before inventing a behaviour.

The ones that most often get violated:

- **No entity in the data model may represent FundLok as a counterparty on a
  facility.** We are not a lender and take no credit risk.
- **The origination total is immutable** and the **outstanding balance is
  derived**, never a mutable field. Extension fees are separate linked ledger
  entries.
- **True-up is relief-only:** `min(scheduled, share × verified_revenue)`. Relief
  extends duration; it never reduces the total owed.
- **The backstop is `1.33 × declared term`**, set at origination; no process may
  move it.
- **Version every rating, method, offer and disclosure** ever shown to a user;
  the audit log is **immutable**; every override records who/why/when/approval.
- **No code path may construct a payment instruction to a FundLok-owned
  account.** Money leaves only to a verified SME account or back to the
  investor.
- **Never build a production dependency on an endpoint we do not control.**

## Core Rules

- If a task matches a skill, you **MUST** invoke it. Do not implement directly when a skill applies.
- Skills live at `.claude/skills/<skill-name>/SKILL.md`. Follow them exactly — do not partially apply.
- Only proceed to implementation after required upstream steps (spec, plan) are complete.

## Intent → Skill Mapping

| When the task is… | Use skill(s) |
| --- | --- |
| Anything touching money, rates, grading, ledger, repayment, disclosure, audit | `fundlok-domain` (always, first) |
| Vague idea / "what should we build" | `interview-me`, `idea-refine` |
| New feature / significant change, no spec yet | `spec-driven-development` → `planning-and-task-breakdown` |
| Breaking work into tasks | `planning-and-task-breakdown` |
| Implementing logic, fixing a bug, changing behavior | `test-driven-development` + `incremental-implementation` |
| Building with a framework/library where correctness matters | `source-driven-development` |
| High-stakes / irreversible / unfamiliar code | `doubt-driven-development` |
| New FastAPI endpoint, Pydantic schema, module boundary | `api-and-interface-design` |
| Bug, failing test, broken build, unexpected behavior | `debugging-and-error-recovery` |
| Reviewing code before merge | `code-review-and-quality` |
| Refactoring for clarity (no behavior change) | `code-simplification` |
| Auth, user input, data storage, payments, third-party integrations | `security-and-hardening` |
| Slow queries, latency, perf regressions | `performance-optimization` |
| Adding logging, metrics, tracing, alerting | `observability-and-instrumentation` |
| Recording an architectural decision | `documentation-and-adrs` |
| Committing, branching, resolving conflicts | `git-workflow-and-versioning` |
| CI/CD pipeline changes | `ci-cd-and-automation` |
| Removing/sunsetting old APIs, migrating users | `deprecation-and-migration` |
| Preparing a production deploy | `shipping-and-launch` |
| Starting a session / configuring context | `context-engineering`, `using-agent-skills` |
| Frontend / browser-rendered work | `frontend-ui-engineering`, `browser-testing-with-devtools` |

## Lifecycle (Phase → Skills)

- **DEFINE** → `interview-me`, `idea-refine`, `spec-driven-development`
- **PLAN** → `planning-and-task-breakdown`
- **BUILD** → `incremental-implementation` + `test-driven-development` + `source-driven-development` + `doubt-driven-development` (+ `api-and-interface-design` for endpoints/schemas)
- **VERIFY** → `debugging-and-error-recovery`, `browser-testing-with-devtools`
- **REVIEW** → `code-review-and-quality`, `code-simplification`, `security-and-hardening`, `performance-optimization`
- **SHIP** → `git-workflow-and-versioning`, `ci-cd-and-automation`, `deprecation-and-migration`, `documentation-and-adrs`, `observability-and-instrumentation`, `shipping-and-launch`

## Slash Commands (Claude Code)

`/spec` · `/plan` · `/build` · `/test` · `/review` · `/code-simplify` · `/ship` · `/webperf` — user-facing entry points that drive the lifecycle above.

## Subagent Personas

Available in `.claude/agents/`: `code-reviewer`, `security-auditor`, `test-engineer`, `web-performance-auditor`.

- Personas may invoke skills; **personas do not invoke other personas**.
- The endorsed multi-persona pattern is **parallel fan-out with a merge step** (used by `/ship`: run `code-reviewer`, `security-auditor`, `test-engineer` concurrently, then synthesize).

## Execution Model

For every request:

1. Determine if any skill applies (even a small chance).
2. Invoke the matching skill before implementing.
3. Follow the skill workflow strictly to its exit criteria.
4. Implement only after required upstream steps are complete.

### Anti-Rationalization

Ignore these thoughts — they are wrong: "this is too small for a skill", "I can just quickly implement this", "I'll gather context first". Always check for and use skills first.

## Project Conventions

- Keep changes incremental and test-backed; this is a fintech codebase.
- New schema changes require an Alembic migration in `alembic/`.
- Run `pytest` before declaring a change done.
- Security-sensitive paths (auth, payments, admin, underwriting) always go through `security-and-hardening` review.
