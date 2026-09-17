from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.underwriting.mapping import to_score_run_out
from app.underwriting.schemas import (
    BankRateConfigCreate,
    BankRateConfigOut,
    ScoreRunApproveOut,
    ScoreRunCreate,
    ScoreRunOut,
    SupportedIndustriesOut,
)
from app.underwriting.service import (
    approve_score_run,
    get_score_run,
    get_supported_industries,
    replay_score_run,
    set_bank_rate,
    start_score_run,
)
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/underwriting", tags=["underwriting"])

require_admin = require_roles(Role.ADMIN)


@router.get("/industries", response_model=SupportedIndustriesOut)
async def get_industries():
    """T3 / Issue 17: served, not transcribed -- Phat's dropdown is
    generated from this response."""
    return get_supported_industries()


@router.post("/score-runs", response_model=ScoreRunOut, status_code=201)
async def post_score_run(
    body: ScoreRunCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sr, grading_result = await start_score_run(db, body)
    append_audit(
        db,
        entity_type="SCORE_RUN",
        entity_id=sr.id,
        action="START",
        actor_id=current_user.id,
        after_state={"status": sr.status, "decision": sr.decision, "application_id": str(sr.application_id)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return to_score_run_out(sr, grading_result)


@router.get("/score-runs/{score_run_id}", response_model=ScoreRunOut)
async def get_score_run_endpoint(
    score_run_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sr, grading_result = await replay_score_run(db, score_run_id)
    return to_score_run_out(sr, grading_result)


@router.post("/score-runs/{score_run_id}/approve", response_model=ScoreRunApproveOut)
async def post_score_run_approve(
    score_run_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sr, is_new = await approve_score_run(db, score_run_id)
    if is_new:
        append_audit(
            db,
            entity_type="SCORE_RUN",
            entity_id=sr.id,
            action="APPROVE_LOCK",
            actor_id=current_user.id,
            after_state={"status": sr.status, "locked_at": str(sr.locked_at)},
            ip_address=request.client.host if request.client else None,
        )
    await db.commit()
    return ScoreRunApproveOut(
        id=sr.id,
        locked_at=sr.locked_at.isoformat() if sr.locked_at else None,
        status=sr.status,
    )


@router.post("/bank-rate", response_model=BankRateConfigOut, status_code=201)
async def post_bank_rate(
    body: BankRateConfigCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """T0b: record a new board-approved bank rate, effective from a given
    date. Never edits an existing row -- see set_bank_rate()."""
    row = await set_bank_rate(db, body.rate_pct, body.effective_from, current_user.id)
    append_audit(
        db,
        entity_type="BANK_RATE_CONFIG",
        entity_id=row.id,
        action="CREATE",
        actor_id=current_user.id,
        after_state={"rate_pct": str(row.rate_pct), "effective_from": str(row.effective_from)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return row
