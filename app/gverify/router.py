"""HTTP router for GVerify (Datatrust) eKYC — direct-API KYC verification.

Spec: docs/specs/gverify/ekyc-kyc-verification.md

Parallel to (not replacing) the Didit `/kyc/*` flow in app/verification/.
GVerify has no hosted UI and no webhook: the investor submits ID images +
portrait in one request and the response carries the final verdict.

Two ways to submit:
  - POST /gverify/kyc/verify          — cookie/Bearer session (same device)
  - POST /gverify/kyc/handoff         — mint a 10-minute handoff token (QR)
    POST /gverify/kyc/handoff/verify  — submit from the phone with that token
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.gverify import kyb_service, service
from app.gverify.client import GVerifyError
from app.gverify.schemas import (
    HandoffResponse,
    KybRepresentative,
    KybStatusResponse,
    KybVerifyRequest,
    KybVerifyResponse,
    KycStatusResponse,
    KycVerifyRequest,
    KycVerifyResponse,
)
from app.gverify.service import ImageValidationError
from app.gverify.tokens import HANDOFF_TTL, create_handoff_token, verify_handoff_token
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/gverify/kyc", tags=["gverify-kyc"])

_authorized = require_roles(Role.INVESTOR)

# KYB — business verification for SMEs (spec: ekyb-kyb-verification.md).
kyb_router = APIRouter(prefix="/gverify/kyb", tags=["gverify-kyb"])

_sme_authorized = require_roles(Role.SME)


async def _run_verification(
    request: Request,
    body: KycVerifyRequest,
    db: AsyncSession,
    user: User,
) -> KycVerifyResponse:
    """Shared verify flow for both the session and handoff-token entrypoints."""
    latest = await service.latest_for_user(db, user.id)
    if latest is not None and latest.is_approved:
        raise HTTPException(status_code=409, detail="KYC is already approved")

    try:
        attempt = await service.run_kyc_verification(
            db,
            user,
            id_front_b64=body.id_front_b64,
            id_back_b64=body.id_back_b64,
            portrait_b64=body.portrait_b64,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except GVerifyError as exc:
        # The FAILED attempt row is already flushed — commit so it's recorded.
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    append_audit(
        db,
        entity_type="GVERIFY_KYC_VERIFICATION",
        entity_id=attempt.id,
        action="VERIFY",
        actor_id=user.id,
        after_state={"status": attempt.status, "person_number": attempt.person_number},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(attempt)

    return KycVerifyResponse(
        verification_id=attempt.id,
        status=attempt.status,
        is_approved=attempt.is_approved,
        rejection_reason=attempt.rejection_reason,
        person_number=attempt.person_number,
        full_name=attempt.full_name,
        date_of_birth=attempt.date_of_birth,
        face_match_score=service.face_match_score(attempt),
        created_at=attempt.created_at,
    )


@router.post("/verify", response_model=KycVerifyResponse, status_code=201)
async def verify(
    request: Request,
    body: KycVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_authorized),
):
    """One-shot KYC: OCR the ID card, face-match the portrait, return the verdict.

    A REJECTED outcome is still 201 — the business verdict is in the body.
    Only provider failures surface as 502 (the attempt is persisted FAILED).
    """
    return await _run_verification(request, body, db, current_user)


@router.post("/handoff", response_model=HandoffResponse, status_code=201)
async def create_handoff(current_user: User = Depends(_authorized)):
    """Mint a short-lived token so the user can continue on their phone.

    The frontend encodes it in a QR; the phone submits the images to
    /gverify/kyc/handoff/verify with `Authorization: Bearer <token>`. The
    token authorizes ONLY that submission and expires after 10 minutes.
    """
    return HandoffResponse(
        token=create_handoff_token(current_user.id),
        expires_in_seconds=int(HANDOFF_TTL.total_seconds()),
    )


@router.post("/handoff/verify", response_model=KycVerifyResponse, status_code=201)
async def verify_via_handoff(
    request: Request,
    body: KycVerifyRequest,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(None),
):
    """Same as /verify, authenticated by a handoff token instead of a session.

    Used by the phone after scanning the desktop QR — the phone has no login
    cookie, only the token minted by /handoff.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing handoff token")
    user_id = verify_handoff_token(authorization.split(" ", 1)[1].strip())

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or user.role != Role.INVESTOR.value:
        raise HTTPException(status_code=401, detail="Invalid or expired handoff token")

    return await _run_verification(request, body, db, user)


@router.get("/status", response_model=KycStatusResponse)
async def get_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_authorized),
):
    """Return the caller's latest GVerify KYC attempt, if any."""
    attempt = await service.latest_for_user(db, current_user.id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="No GVerify KYC verification found")
    return KycStatusResponse(
        verification_id=attempt.id,
        status=attempt.status,
        is_terminal=attempt.is_terminal,
        is_approved=attempt.is_approved,
        rejection_reason=attempt.rejection_reason,
        person_number=attempt.person_number,
        full_name=attempt.full_name,
        updated_at=attempt.updated_at,
    )


# --------------------------------------------------------------------------- #
# KYB — business verification (SME)
# --------------------------------------------------------------------------- #


@kyb_router.post("/verify", response_model=KybVerifyResponse, status_code=201)
async def kyb_verify(
    request: Request,
    body: KybVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_sme_authorized),
):
    """One-shot KYB: OCR the registration certificate, cross-check the tax
    code against the state registry, return the verdict.

    A REJECTED outcome is still 201 — the business verdict is in the body.
    Only provider failures surface as 502 (the attempt is persisted FAILED).
    """
    latest = await kyb_service.latest_for_user(db, current_user.id)
    if latest is not None and latest.is_approved:
        raise HTTPException(status_code=409, detail="KYB is already approved")

    try:
        attempt = await kyb_service.run_kyb_verification(
            db,
            current_user,
            document_b64=body.document_b64,
            document_type=body.document_type,
            declared_tax_code=body.tax_code,
        )
    except ImageValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except GVerifyError as exc:
        # The FAILED attempt row is already flushed — commit so it's recorded.
        await db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    append_audit(
        db,
        entity_type="GVERIFY_KYB_VERIFICATION",
        entity_id=attempt.id,
        action="VERIFY",
        actor_id=current_user.id,
        after_state={"status": attempt.status, "tax_code": attempt.tax_code},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(attempt)

    return KybVerifyResponse(
        verification_id=attempt.id,
        status=attempt.status,
        is_approved=attempt.is_approved,
        rejection_reason=attempt.rejection_reason,
        tax_code=attempt.tax_code,
        business_name=attempt.business_name,
        business_type=attempt.business_type,
        business_status=kyb_service.business_status(attempt),
        representatives=[
            KybRepresentative(
                name=rep.get("name"),
                # Live payloads use identity_number/position; the API doc said
                # id_number/title — accept both.
                id_number=rep.get("identity_number") or rep.get("id_number"),
                title=rep.get("position") or rep.get("title"),
            )
            for rep in (attempt.representatives or [])
        ],
        created_at=attempt.created_at,
    )


@kyb_router.get("/status", response_model=KybStatusResponse)
async def kyb_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(_sme_authorized),
):
    """Return the caller's latest GVerify KYB attempt, if any."""
    attempt = await kyb_service.latest_for_user(db, current_user.id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="No GVerify KYB verification found")
    return KybStatusResponse(
        verification_id=attempt.id,
        status=attempt.status,
        is_terminal=attempt.is_terminal,
        is_approved=attempt.is_approved,
        rejection_reason=attempt.rejection_reason,
        tax_code=attempt.tax_code,
        business_name=attempt.business_name,
        updated_at=attempt.updated_at,
    )
