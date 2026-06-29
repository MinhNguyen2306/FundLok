"""HTTP routers for identity/business verification (Didit).

A single module serves both flows from shared logic:
  - kyc_router  -> /kyc/*  (individual identity, INVESTOR only) + the Didit webhook
  - kyb_router  -> /kyb/*  (business verification, SME only)

The flows share one table and the Sessions-API plumbing in this package; they
differ only by the workflow run, the stored verification_type, and the role
allowed to start them. The Didit webhook is not type-specific (keyed by
session_id), so a single /kyc/webhook endpoint handles both.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles
from app.verification import service
from app.verification.client import DiditError
from app.verification.schemas import StartRequest, StartResponse, StatusResponse


def _to_status(v) -> StatusResponse:
    return StatusResponse(
        verification_id=v.id,
        session_id=v.session_id,
        status=v.status,
        verification_type=v.verification_type,
        is_terminal=v.is_terminal,
        is_approved=v.is_approved,
        verification_url=v.verification_url,
        updated_at=v.updated_at,
    )


def build_verification_router(
    *, prefix: str, tag: str, verification_type: str, role: Role
) -> APIRouter:
    """Build a role-gated router for a single Didit flow (KYC or KYB).

    Both flows expose identical start/status/sync endpoints; they are generated
    here so the contract and behavior stay in lockstep. The caller registers
    the returned router and (for KYC) attaches the shared webhook.
    """
    router = APIRouter(prefix=prefix, tags=[tag])
    entity_type = f"{verification_type}_VERIFICATION"
    authorized = require_roles(role)

    @router.post("/start", response_model=StartResponse, status_code=201)
    def start(
        request: Request,
        body: StartRequest | None = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(authorized),
    ):
        """Create (or reuse) a Didit session and return the hosted URL.

        Optional body: `{"language": "vi"}` — the user's locale from the
        frontend. Falls back to the DIDIT_LANGUAGE env default when omitted.
        """
        try:
            verification = service.start_verification(
                db,
                current_user,
                verification_type=verification_type,
                language=body.language if body else None,
            )
        except DiditError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
            )

        append_audit(
            db,
            entity_type=entity_type,
            entity_id=verification.id,
            action="START",
            actor_id=current_user.id,
            after_state={
                "session_id": verification.session_id,
                "status": verification.status,
            },
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        db.refresh(verification)
        return StartResponse(
            verification_id=verification.id,
            session_id=verification.session_id,
            status=verification.status,
            verification_url=verification.verification_url,
        )

    @router.get("/status", response_model=StatusResponse)
    def get_status(
        db: Session = Depends(get_db),
        current_user: User = Depends(authorized),
    ):
        """Return the current user's latest verification of this type, if any."""
        verification = service.get_status(db, current_user, verification_type)
        if verification is None:
            raise HTTPException(
                status_code=404, detail=f"No {verification_type} verification found"
            )
        return _to_status(verification)

    @router.post("/sync", response_model=StatusResponse)
    def sync(
        db: Session = Depends(get_db),
        current_user: User = Depends(authorized),
    ):
        """Pull the latest decision from Didit for the user's session (FE poll fallback)."""
        verification = service.get_status(db, current_user, verification_type)
        if verification is None:
            raise HTTPException(
                status_code=404, detail=f"No {verification_type} verification found"
            )
        try:
            verification = service.sync_verification(db, verification)
        except DiditError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)
            )
        db.commit()
        db.refresh(verification)
        return _to_status(verification)

    return router


# KYC — individual identity verification, investors only.
kyc_router = build_verification_router(
    prefix="/kyc", tag="kyc", verification_type="KYC", role=Role.INVESTOR
)

# KYB — business verification, SMEs only.
kyb_router = build_verification_router(
    prefix="/kyb", tag="kyb", verification_type="KYB", role=Role.SME
)


@kyc_router.post("/webhook", status_code=200)
async def webhook(request: Request, db: Session = Depends(get_db)):
    """Receive Didit verification webhooks (both KYC and KYB).

    The webhook is keyed by session_id, so a single endpoint handles every
    flow. The raw body must be read and HMAC-verified BEFORE parsing, so the
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
            entity_type=f"{verification.verification_type}_VERIFICATION",
            entity_id=verification.id,
            action="WEBHOOK",
            actor_id=None,
            after_state={"status": verification.status},
        )
        db.commit()
    # Always 200 so Didit does not retry on unknown/stale sessions.
    return {"received": True}
