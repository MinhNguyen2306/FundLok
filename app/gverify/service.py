"""GVerify eKYC business logic — one-shot OCR + face-match verification.

Spec: docs/specs/gverify/ekyc-kyc-verification.md

Unlike the Didit flow (hosted session + webhook), GVerify is a direct API:
we submit the images and get a synchronous verdict. Each call to
run_kyc_verification creates ONE attempt row that ends terminal within the
same request (APPROVED / REJECTED / FAILED). Retries after rejection are new
rows; the newest row per user is the current state.

Images are validated (base64, JPEG/PNG magic bytes, <= 10MB decoded) before
any provider call, held in memory only, and never persisted.
"""
from __future__ import annotations

import base64
import binascii

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.gverify import client, storage
from app.gverify.models import (
    STATUS_APPROVED,
    STATUS_FAILED,
    STATUS_PENDING,
    STATUS_REJECTED,
    GVerifyVerification,
)
from app.users.models import User

_MAX_IMAGE_BYTES = 10 * 1024 * 1024  # GVerify's documented per-image limit

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Values GVerify uses for the front_valid/back_valid flags (strings in the
# doc); we accept common truthy spellings case-insensitively plus real bools.
_TRUTHY = {"true", "1", "yes", "valid"}


class ImageValidationError(ValueError):
    """A submitted image failed base64/format/size validation (caller error)."""


def _validate_image(name: str, b64: str) -> tuple[str, bytes]:
    """Check one base64 image; returns the (stripped) base64 string + raw bytes."""
    b64 = (b64 or "").strip()
    if not b64:
        raise ImageValidationError(f"{name} is empty")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ImageValidationError(f"{name} is not valid base64")
    if len(raw) > _MAX_IMAGE_BYTES:
        raise ImageValidationError(f"{name} exceeds the 10MB limit")
    if not (raw.startswith(_JPEG_MAGIC) or raw.startswith(_PNG_MAGIC)):
        raise ImageValidationError(f"{name} must be a JPEG or PNG image")
    return b64, raw


def _is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in _TRUTHY
    return False


def _as_float(value) -> float | None:
    """Parse GVerify's stringly-typed scores; None when unparseable/absent."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ocr_rejection_reason(data: dict) -> str | None:
    """Apply the OCR pass rules (spec §6.3); returns a reason or None if OK."""
    if not _is_truthy(data.get("front_valid")):
        detail = data.get("front_invalid_message")
        return f"ID card front not valid{f': {detail}' if detail else ''}"
    if not _is_truthy(data.get("back_valid")):
        detail = data.get("back_invalid_message")
        return f"ID card back not valid{f': {detail}' if detail else ''}"
    if not (data.get("person_number") or "").strip():
        return "Could not extract the ID number from the card"

    minimum = settings.GVERIFY_MIN_OCR_CONFIDENCE
    for field in ("person_number_confidence", "full_name_confidence"):
        score = _as_float(data.get(field))
        if score is not None and score < minimum:
            return f"OCR confidence too low ({field.removesuffix('_confidence')})"
    return None


def _face_rejection_reason(data: dict) -> str | None:
    """Apply the face-match pass rule (spec §6.4); returns a reason or None.

    The verdict rests SOLELY on the provider's ``is_matching`` flag. Observed
    live (TPVDEMO, 2026-07-15): ``match`` is a binary mirror of is_matching
    ("1"/"0"), and ``matching`` is the similarity percentage — both kept in
    face_data for audit/display, neither re-thresholded by us. The biometric
    warning (invalid_code/invalid_message) is advisory only: it fires
    naturally when one input is a document photo (Datatrust guidance).
    """
    if not data.get("is_matching"):
        return "Portrait does not match the ID card photo"
    return None


async def latest_for_user(
    db: AsyncSession, user_id, verification_type: str = "KYC"
) -> GVerifyVerification | None:
    result = await db.execute(
        select(GVerifyVerification)
        .where(
            GVerifyVerification.user_id == user_id,
            GVerifyVerification.verification_type == verification_type,
        )
        .order_by(GVerifyVerification.created_at.desc())
    )
    return result.scalars().first()


async def run_kyc_verification(
    db: AsyncSession,
    user: User,
    *,
    id_front_b64: str,
    id_back_b64: str,
    portrait_b64: str,
) -> GVerifyVerification:
    """Run the full one-shot KYC flow and return the terminal attempt row.

    Raises ImageValidationError (caller error, no row created) or
    client.GVerifyError (provider failure — the attempt row is left FAILED;
    the caller must still commit so the failure is recorded).
    """
    front, front_raw = _validate_image("id_front_b64", id_front_b64)
    back, back_raw = _validate_image("id_back_b64", id_back_b64)
    portrait, portrait_raw = _validate_image("portrait_b64", portrait_b64)

    attempt = GVerifyVerification(user_id=user.id, status=STATUS_PENDING)
    db.add(attempt)
    await db.flush()

    # Retain the submitted documents under verification/KYC/<attempt-id>/ —
    # best-effort; the attempt proceeds even if storage is down.
    await storage.store_kyc_documents(
        attempt.id, id_front=front_raw, id_back=back_raw, portrait=portrait_raw
    )

    try:
        ocr = await client.verify_ocr_id(img_front_b64=front, img_back_b64=back)
    except client.GVerifyError as exc:
        attempt.status = STATUS_FAILED
        attempt.rejection_reason = str(exc)
        await db.flush()
        raise

    attempt.ocr_transaction_code = ocr.get("transaction_code")
    attempt.ocr_data = ocr
    attempt.person_number = ocr.get("person_number")
    attempt.full_name = ocr.get("full_name")
    attempt.date_of_birth = ocr.get("date_of_birth")

    reason = _ocr_rejection_reason(ocr)
    if reason is not None:
        # Fail fast: skip the (billable) face-match call on an invalid card.
        attempt.status = STATUS_REJECTED
        attempt.rejection_reason = reason
        await db.flush()
        return attempt

    try:
        # Image order per partner testing (2026-07-15): img1 = ID-card front,
        # img2 = live portrait.
        face = await client.face_match(img1_b64=front, img2_b64=portrait)
    except client.GVerifyError as exc:
        attempt.status = STATUS_FAILED
        attempt.rejection_reason = str(exc)
        await db.flush()
        raise

    attempt.face_transaction_code = face.get("transaction_code")
    attempt.face_data = face

    reason = _face_rejection_reason(face)
    if reason is not None:
        attempt.status = STATUS_REJECTED
        attempt.rejection_reason = reason
    else:
        attempt.status = STATUS_APPROVED
    await db.flush()
    return attempt


def face_match_score(attempt: GVerifyVerification) -> float | None:
    """The 0-1 face-similarity of an attempt, when the face step ran.

    Sourced from ``matching`` (a percentage — the real similarity signal);
    falls back to ``match`` for older attempts recorded before we learned
    that field is binary.
    """
    if not attempt.face_data:
        return None
    percent = _as_float(attempt.face_data.get("matching"))
    if percent is not None:
        return round(percent / 100, 4)
    return _as_float(attempt.face_data.get("match"))
