import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.system.models import SystemSetting
from app.system.schemas import MaintenanceState

# Key used in the system_settings table for the maintenance toggle.
MAINTENANCE_KEY = "maintenance_mode"


async def get_maintenance(db: AsyncSession) -> MaintenanceState:
    row = await db.get(SystemSetting, MAINTENANCE_KEY)
    if row is None:
        return MaintenanceState(enabled=False)
    value = row.value or {}
    return MaintenanceState(
        enabled=bool(value.get("enabled", False)),
        message=value.get("message"),
        updated_at=row.updated_at,
        updated_by=row.updated_by,
    )


async def set_maintenance(
    db: AsyncSession, *, enabled: bool, message: str | None, actor_id: UUID | None
) -> MaintenanceState:
    value = {"enabled": enabled, "message": message}
    row = await db.get(SystemSetting, MAINTENANCE_KEY)
    if row is None:
        row = SystemSetting(
            key=MAINTENANCE_KEY,
            value=value,
            description="Global maintenance-mode toggle",
            updated_by=actor_id,
        )
        db.add(row)
    else:
        row.value = value
        row.updated_by = actor_id
    await db.commit()
    _invalidate_maintenance_cache()
    return await get_maintenance(db)


# --- Lightweight cache so the request middleware doesn't hit the DB every call.
_MAINT_TTL_SECONDS = 5.0
_maint_cache: dict = {"value": None, "ts": 0.0}


def _invalidate_maintenance_cache() -> None:
    _maint_cache["value"] = None
    _maint_cache["ts"] = 0.0


async def is_maintenance_active() -> tuple[bool, str | None]:
    """(enabled, message) for the middleware. Cached for a few seconds.

    HANDOFF-02 Fix A: this now opens its own AsyncSession via `async with
    SessionLocal()` instead of the old sync `SessionLocal(); ...; db.close()`
    pattern -- still independent of the `get_db` request dependency (that
    part of the original design is unchanged), just async now.
    """
    now = time.monotonic()
    if _maint_cache["value"] is None or now - _maint_cache["ts"] > _MAINT_TTL_SECONDS:
        async with SessionLocal() as db:
            state = await get_maintenance(db)
            _maint_cache["value"] = (state.enabled, state.message)
        _maint_cache["ts"] = now
    return _maint_cache["value"]
