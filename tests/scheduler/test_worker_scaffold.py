"""T2 (HANDOFF-03 Issue 8) -- ARQ worker scaffold.

These tests exercise the WorkerSettings registration and the job functions
directly (no live Redis / arq run loop -- conftest.py's guardrail is never
hit a real external dependency in tests). A real end-to-end "does the arq
worker process actually fire this on schedule against real Redis" check is
an infra/ops smoke test, not a unit test, and is out of scope here; T2's
acceptance criterion is that this scaffold is wired correctly, which does
not require a running broker to verify.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.core.timezone import ICT
from app.scheduler.jobs import daily_batch_placeholder, health_check
from app.scheduler.worker import WorkerSettings


def test_ict_timezone_is_utc_plus_7_with_no_dst():
    now = datetime(2026, 1, 1, tzinfo=ICT)
    assert now.utcoffset().total_seconds() == 7 * 3600
    # Vietnam has observed a fixed UTC+7 with no DST since 1975 -- assert
    # the offset is identical in both a nominal winter and summer month, so
    # a future zoneinfo database update introducing DST would fail this
    # loudly rather than silently shifting every facility's day boundary.
    winter = datetime(2026, 1, 15, tzinfo=ICT).utcoffset()
    summer = datetime(2026, 7, 15, tzinfo=ICT).utcoffset()
    assert winter == summer


async def test_health_check_job_returns_ok():
    result = await health_check(ctx={})
    assert result == "ok"


async def test_daily_batch_placeholder_job_returns_ok():
    result = await daily_batch_placeholder(ctx={})
    assert result == "ok"


def test_worker_settings_registers_both_jobs():
    names = {fn.__name__ for fn in WorkerSettings.functions}
    assert names == {"health_check", "daily_batch_placeholder"}


def test_worker_settings_uses_ict_timezone_explicitly():
    # ARQ has no per-cron-job timezone -- only a worker-level one -- so this
    # is the one place that has to be right for every cron job on this
    # worker to be ICT-scheduled.
    assert WorkerSettings.timezone == ICT
    assert WorkerSettings.timezone != timezone.utc


def test_daily_batch_cron_is_a_single_instant_not_a_window_spanning_midnight():
    """Repayment spec §14: the daily batch window must be explicit and must
    not straddle midnight. Registered as hour=0, minute=5 -- one fixed
    instant just after midnight ICT, never a range that itself crosses the
    day boundary."""
    assert len(WorkerSettings.cron_jobs) == 1
    job = WorkerSettings.cron_jobs[0]
    assert job.hour == 0
    assert job.minute == 5
    # A single (hour, minute) pair cannot itself span two calendar days --
    # unlike, say, a 23:30-00:30 window, which would.
    assert job.coroutine.__name__ == "daily_batch_placeholder"


def test_redis_settings_derived_from_settings_redis_url(monkeypatch):
    import importlib

    monkeypatch.setenv("REDIS_URL", "redis://example-redis-host:6380/2")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    monkeypatch.setenv("SECRET_KEY", "test")

    import app.core.config as config_module

    importlib.reload(config_module)
    import app.scheduler.worker as worker_module

    importlib.reload(worker_module)

    assert worker_module.WorkerSettings.redis_settings.host == "example-redis-host"
    assert worker_module.WorkerSettings.redis_settings.port == 6380
    assert worker_module.WorkerSettings.redis_settings.database == 2

    # Restore the module-level singletons other tests rely on.
    monkeypatch.delenv("REDIS_URL", raising=False)
    importlib.reload(config_module)
    importlib.reload(worker_module)
