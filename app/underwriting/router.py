from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.underwriting.schemas import ScoreRunApproveOut, ScoreRunCreate, ScoreRunOut
from app.underwriting.service import approve_score_run, start_score_run
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/underwriting", tags=["underwriting"])

require_admin = require_roles(Role.ADMIN)


@router.post("/score-runs", response_model=ScoreRunOut, status_code=201)
def post_score_run(
    body: ScoreRunCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sr = start_score_run(db, body.application_id, body.mode)
    append_audit(
        db,
        entity_type="SCORE_RUN",
        entity_id=sr.id,
        action="START",
        actor_id=current_user.id,
        after_state={"status": sr.status, "application_id": str(sr.application_id)},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return sr


@router.post("/score-runs/{score_run_id}/approve", response_model=ScoreRunApproveOut)
def post_score_run_approve(
    score_run_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    sr, is_new = approve_score_run(db, score_run_id)
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
    db.commit()
    return ScoreRunApproveOut(
        id=sr.id,
        locked_at=sr.locked_at.isoformat() if sr.locked_at else None,
        status=sr.status,
    )
