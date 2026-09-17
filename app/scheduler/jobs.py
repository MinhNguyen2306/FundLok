"""ARQ job functions (T2, HANDOFF-03 Issue 8).

`app/scheduler/worker.py` registers these on the ARQ `WorkerSettings`. Every
job takes `ctx` (the ARQ job context dict) first, per ARQ's calling
convention -- see https://arq-docs.helpmanual.io/.

Only a health check and a no-op daily placeholder live here today. The real
daily repayment cycle (reminders, cutoff, arrears escalation, backstop
evaluation -- spec §6.2) is T11 and depends on the facility model (T6),
state machine (T9) and business-day calendar (T8) this handoff also builds;
`daily_batch_placeholder` is the registration seam T11 replaces, not a
stand-in for its logic.
"""
import logging
from datetime import datetime
from typing import Any

from app.core.timezone import ICT

logger = logging.getLogger("app.scheduler")


async def health_check(ctx: dict[str, Any]) -> str:
    """Liveness job: proves the worker process is up, connected to Redis,
    and able to execute a job end to end. Not itself a health *endpoint* --
    ops can enqueue this on demand, or watch it run at startup."""
    now_ict = datetime.now(ICT)
    logger.info("scheduler.health_check ok at %s", now_ict.isoformat())
    return "ok"


async def daily_batch_placeholder(ctx: dict[str, Any]) -> str:
    """Fires once a day at the ICT daily batch window (see worker.py). A
    deliberate no-op today -- T2's acceptance criterion is that this job
    fires and logs on schedule with ICT timestamps; T11 is what makes it do
    anything to a facility. Kept as its own function (rather than inlining
    real logic later) so the cron registration in worker.py never has to
    change, only this function's body.
    """
    now_ict = datetime.now(ICT)
    logger.info("scheduler.daily_batch_placeholder fired at %s (no-op, pending T11)", now_ict.isoformat())
    return "ok"
