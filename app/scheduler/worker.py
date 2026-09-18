"""ARQ worker scaffold (T2, HANDOFF-03 Issue 8).

Run with: `arq app.scheduler.worker.WorkerSettings`
(the `worker` service in docker-compose.yml does exactly this).

Design notes
------------
- Redis URL comes from `settings.REDIS_URL` (env-driven, like every other
  external dependency in `app/core/config.py`) -- never hardcoded.
- `timezone=ICT` on `WorkerSettings` makes every `cron()` job's hour/minute
  fields evaluate against Asia/Ho_Chi_Minh explicitly, regardless of the
  host machine's local timezone. ARQ has no separate per-job tz parameter;
  the worker-level `timezone` is the only knob, so every cron job on this
  worker is implicitly ICT-scheduled by construction.
- The daily batch job fires at 00:05 ICT: repayment spec §14 requires the
  batch window to be "explicit" and to "not straddle midnight" -- a single
  fixed instant just after midnight (rather than, say, a 23:30-00:30
  window that would itself span two calendar days) satisfies both: it is
  unambiguous and it never disagrees with itself about which business day
  it is running for.
"""
from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings
from app.core.timezone import ICT
from app.scheduler.jobs import daily_batch_placeholder, health_check


class WorkerSettings:
    functions = [health_check, daily_batch_placeholder]
    cron_jobs = [
        cron(daily_batch_placeholder, hour=0, minute=5, run_at_startup=False),
    ]
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    timezone = ICT
    # Fine for the T2 scaffold's single no-op job; T11's real daily batch
    # (per-facility reminders/cutoff/arrears/backstop) will need its own
    # per-job timeout/max_tries tuning once it exists.
    job_timeout = 300
    max_jobs = 10
