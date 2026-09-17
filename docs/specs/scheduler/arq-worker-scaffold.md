# Spec: ARQ Worker Scaffold

| Field | Value |
|---|---|
| **Status** | ACCEPTED |
| **Owner** | Edward |
| **Implementer(s)** | Edward (backend) |
| **Module** | `app/scheduler/` |
| **Version** | 1.0 |
| **Date** | 2026-09-17 |
| **Related ADR** | — |
| **Depends on** | — |

---

## 1. Context & Goal

HANDOFF-03 Issue 8: there is no scheduler anywhere in the codebase -- no
ARQ worker, no cron, nothing in `requirements.txt` -- and the entire
repayment mechanic (T11) is a daily batch: reminder emission at day open,
cutoff evaluation, arrears escalation, backstop evaluation. `CLAUDE.md`
already names ARQ as the async task queue and forbids `BackgroundTasks` for
financial operations, so this stands up the worker process itself, ahead
of any job that has real financial behaviour.

**Goal:** an ARQ worker that starts under docker-compose, connects to
Redis, runs a health-check job, and has one job registered on an explicit,
non-midnight-straddling ICT cron schedule -- the seam T11 plugs its real
daily-batch logic into without touching the registration.

---

## 2. Out of Scope

- The actual daily repayment cycle (reminders, cutoff, arrears escalation,
  backstop evaluation) -- that is T11, and depends on T6 (facility model),
  T8 (business-day calendar) and T9 (state machine), none of which exist
  yet at T2.
- ML scoring jobs (mentioned in `CLAUDE.md`'s worker description) -- no
  spec or task calls for moving grading onto ARQ in this handoff.
- Any job-level retry/alerting policy beyond ARQ's defaults.

---

## 3. Data Model

No schema changes. No new tables.

---

## 4. API Contract

No HTTP endpoints. This spec's surface is:

- `app/scheduler/worker.py::WorkerSettings` -- the ARQ entrypoint, run via
  `arq app.scheduler.worker.WorkerSettings`.
- `app/scheduler/jobs.py::health_check(ctx)` -- liveness job.
- `app/scheduler/jobs.py::daily_batch_placeholder(ctx)` -- no-op, cron-fired.
- `Settings.REDIS_URL` (`app/core/config.py`) -- new env-driven setting,
  default `redis://localhost:6379/0`.
- `app/core/timezone.py::ICT` -- shared `zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")`
  constant, used by the worker's `timezone` setting and by every future
  job that needs an ICT-anchored timestamp.

---

## 5. State Machine

Not applicable.

---

## 6. Business Rules

1. Every scheduled job's timestamps are Asia/Ho_Chi_Minh (spec §14), never
   UTC or host-local time. ARQ has no per-`cron()`-job timezone parameter --
   only a worker-level `timezone` setting -- so `WorkerSettings.timezone`
   is set to `ICT` once, and every `cron()` job's `hour`/`minute` fields on
   this worker are ICT by construction.
2. The daily batch fires at a single fixed instant (00:05 ICT), not a
   window. §14 requires the batch window to be explicit and to not
   straddle midnight; a 23:30-00:30-style window would itself span two
   calendar days and make "which business day is this batch for"
   ambiguous. A single (hour, minute) pair cannot straddle anything.
3. Background/scheduled financial-adjacent work goes through ARQ, never
   FastAPI's `BackgroundTasks` (CLAUDE.md) -- this scaffold is the only
   sanctioned entrypoint for it going forward.

---

## 7. Error Cases

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Redis unreachable at worker startup | ARQ worker process fails to start / retries per its own connection logic | — (ops-visible via process exit / logs, not a caller-facing path) |
| `daily_batch_placeholder` raises | ARQ's default retry/backoff applies (`max_tries` default) | — (async, no caller) |

---

## 8. Acceptance Criteria

- [x] `test_worker_settings_registers_both_jobs` -- `health_check` and `daily_batch_placeholder` are both registered
- [x] `test_worker_settings_uses_ict_timezone_explicitly` -- worker timezone is ICT, not UTC
- [x] `test_daily_batch_cron_is_a_single_instant_not_a_window_spanning_midnight` -- cron is one (hour, minute) pair
- [x] `test_health_check_job_returns_ok`, `test_daily_batch_placeholder_job_returns_ok` -- both jobs run and log
- [x] `test_redis_settings_derived_from_settings_redis_url` -- `REDIS_URL` is read from settings, not hardcoded
- [x] `arq` worker starts in docker-compose (`worker` service added, depends on `postgres` + `redis` health)

---

## 9. Open Questions

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | Should ML scoring (T3/T4) move onto this worker in a later handoff? | Edward | Not decided -- out of scope here. |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-09-17 | Edward | Initial ARQ scaffold (T2, HANDOFF-03). |
