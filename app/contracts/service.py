from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.lending.models import Contract, LoanApplication, ScoreRun
from app.contracts.schemas import ContractCreate


def create_contract(db: Session, body: ContractCreate) -> Contract:
    sr = db.query(ScoreRun).filter(ScoreRun.id == body.score_run_id).first()
    if not sr or sr.status != "LOCKED":
        raise HTTPException(
            status_code=400,
            detail="Score run must exist and be LOCKED",
        )
    app = db.query(LoanApplication).filter(LoanApplication.id == body.application_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    if sr.application_id != app.id:
        raise HTTPException(status_code=400, detail="Score run does not match application")
    terms = dict(sr.recommended_terms or {})
    if body.template_version:
        terms["template_version"] = body.template_version
    c = Contract(
        application_id=app.id,
        score_run_id=sr.id,
        status="ACTIVE_PENDING_FUNDING",
        final_terms=terms,
        target_amount=app.requested_amount,
        funded_amount=0,
    )
    db.add(c)
    db.flush()
    db.refresh(c)
    return c
