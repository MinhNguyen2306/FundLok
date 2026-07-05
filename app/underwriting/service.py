from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.lending.models import LoanApplication, ScoreRun


async def start_score_run(
    db: AsyncSession,
    application_id: UUID,
    mode: str | None,
) -> ScoreRun:
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == application_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if app.status != "SUBMITTED":
        raise HTTPException(
            status_code=400,
            detail="Application must be in SUBMITTED status before scoring",
        )
    sr = ScoreRun(application_id=application_id, status="RUNNING")
    db.add(sr)
    await db.flush()
    # MVP: complete synchronously
    app.status = "UNDER_REVIEW"
    sr.status = "READY"
    sr.overall_score = Decimal("72.50")
    sr.risk_grade = "B"
    sr.recommended_terms = {"mode": mode or "default", "rate": "12%"}
    sr.factor_results = {"mock": True}
    db.add(app)
    db.add(sr)
    await db.flush()
    await db.refresh(sr)
    return sr


async def approve_score_run(db: AsyncSession, score_run_id: UUID) -> tuple[ScoreRun, bool]:
    result = await db.execute(select(ScoreRun).where(ScoreRun.id == score_run_id))
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Score run not found")
    if sr.status == "LOCKED":
        return sr, False
    if sr.status != "READY":
        raise HTTPException(status_code=400, detail="Score run must be READY to approve")
    sr.status = "LOCKED"
    sr.locked_at = datetime.now(timezone.utc)
    db.add(sr)
    await db.flush()
    await db.refresh(sr)
    return sr, True
