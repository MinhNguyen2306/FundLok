from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.kyc import service
from app.kyc.client import DiditError
from app.kyc.schemas import KycStartResponse, KycStatusResponse
from app.users.models import User
from app.utils.audit import append_audit
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/kyc", tags=["kyc"])


def _to_status(v) -> KycStatusResponse:
    return KycStatusResponse(
        verification_id=v.id,
        session_id=v.session_id,
        status=v.status,
        is_terminal=v.is_terminal,
        is_approved=v.is_approved,
        verification_url=v.verification_url,
        updated_at=v.updated_at,
    )


@router.post("/start", response_model=KycStartResponse, status_code=201)
def start_kyc(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create (or reuse) a Didit KYC session and return the hosted verification URL."""
    try:
        verification = service.start_verification(db, current_user)
    except DiditError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    append_audit(
        db,
        entity_type="KYC_VERIFICATION",
        entity_id=verification.id,
        action="START",
        actor_id=current_user.id,
        after_state={"session_id": verification.session_id, "status": verification.status},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(verification)
    return KycStartResponse(
        verification_id=verification.id,
        session_id=verification.session_id,
        status=verification.status,
        verification_url=verification.verification_url,
    )


@router.get("/status", response_model=KycStatusResponse)
def kyc_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's latest KYC verification, if any."""
    verification = service.get_status(db, current_user)
    if verification is None:
        raise HTTPException(status_code=404, detail="No KYC verification found")
    return _to_status(verification)


@router.post("/sync", response_model=KycStatusResponse)
def sync_kyc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pull the latest decision from Didit for the user's session (FE poll fallback)."""
    verification = service.get_status(db, current_user)
    if verification is None:
        raise HTTPException(status_code=404, detail="No KYC verification found")
    try:
        verification = service.sync_verification(db, verification)
    except DiditError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    db.commit()
    db.refresh(verification)
    return _to_status(verification)


@router.post("/webhook", status_code=200)
async def kyc_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive Didit verification webhooks.

    The raw body must be read and HMAC-verified BEFORE parsing, so the
    signature is computed over the exact transmitted bytes. Unauthenticated —
    trust is established by the signature, not a bearer token.
    """
    raw_body = await request.body()
    if not service.verify_webhook(raw_body, dict(request.headers)):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json

    try:
        payload = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Idempotency: Didit redelivers on failure — skip if we've seen this event.
    if service.already_processed(db, payload.get("event_id")):
        return {"received": True, "duplicate": True}

    verification = service.handle_webhook(db, payload)
    if verification is not None:
        append_audit(
            db,
            entity_type="KYC_VERIFICATION",
            entity_id=verification.id,
            action="WEBHOOK",
            actor_id=None,
            after_state={"status": verification.status},
        )
        db.commit()
    # Always 200 so Didit does not retry on unknown/stale sessions.
    return {"received": True}
