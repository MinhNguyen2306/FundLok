"""GVerify eKYB business logic — certificate OCR + tax-registry cross-check.

Spec: docs/specs/gverify/ekyb-kyb-verification.md

One call to run_kyb_verification creates ONE attempt row that ends terminal
within the same request (APPROVED / REJECTED / FAILED):

  1. OCR X reads the business registration certificate (JPEG/PNG/PDF)
  2. Tax Code Verify checks the extracted tax code against the state registry
  3. Cross-checks: registry valid + business active, OCR name == registry
     name, and (flag-gated) the SME's KYC-verified person appears among the
     certificate's legal representatives.

The certificate is held in memory only and never persisted.
"""
from __future__ import annotations

import base64
import binascii
import unicodedata

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.gverify import client, storage
from app.gverify.models import (
    STATUS_APPROVED,
    STATUS_FAILED,
    STATUS_MANUAL_REVIEW,
    STATUS_PENDING,
    STATUS_REJECTED,
    GVerifyKybVerification,
    GVerifyVerification,
)
from app.gverify.service import ImageValidationError, _as_float
from app.users.models import User

_MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_PDF_MAGIC = b"%PDF"

# Per the provider integration guide, OCR X business verification covers
# company and branch certificates. (HOUSEHOLD dropped 2026-07-15 — resolves
# spec Open Question 3.)
DOCUMENT_TYPES = ("COMPANY", "COMPANY_BRANCH")

# Registry statuses that count as an operating business (Open Question 1 —
# matched case-insensitively until Datatrust confirms the enumeration).
_ACTIVE_STATUSES = ("đang hoạt động", "active")


def _validate_document(b64: str) -> tuple[bytes, str, str]:
    """Validate the certificate; returns (bytes, filename, content_type)."""
    b64 = (b64 or "").strip()
    if not b64:
        raise ImageValidationError("document_b64 is empty")
    try:
        raw = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError):
        raise ImageValidationError("document_b64 is not valid base64")
    if len(raw) > _MAX_DOCUMENT_BYTES:
        raise ImageValidationError("document exceeds the 10MB limit")
    if raw.startswith(_JPEG_MAGIC):
        return raw, "certificate.jpg", "image/jpeg"
    if raw.startswith(_PNG_MAGIC):
        return raw, "certificate.png", "image/png"
    if raw.startswith(_PDF_MAGIC):
        return raw, "certificate.pdf", "application/pdf"
    raise ImageValidationError("document must be a JPEG, PNG or PDF")


def _normalize_name(value: str | None) -> str:
    """Case-, diacritic- and whitespace-insensitive form for name comparison."""
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFD", value)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    # Vietnamese Đ/đ doesn't decompose to D via NFD — map it explicitly.
    stripped = stripped.replace("Đ", "D").replace("đ", "d")
    return " ".join(stripped.casefold().split())


def _ocr_rejection_reason(data: dict) -> str | None:
    """Hard OCR failures (unreadable document) — REJECTED."""
    if not (data.get("name") or "").strip():
        return "Could not extract the business name from the certificate"
    if not (data.get("tax_code") or "").strip():
        return "Could not extract the tax code from the certificate"
    return None


def _ocr_review_reason(data: dict) -> str | None:
    """Soft OCR signals — MANUAL_REVIEW per the provider integration guide
    (low confidence is a review case, not a rejection)."""
    minimum = settings.GVERIFY_MIN_KYB_OCR_CONFIDENCE
    for field in ("name_confidence", "tax_code_confidence"):
        score = _as_float(data.get(field))
        if score is not None and score < minimum:
            return f"OCR confidence too low ({field.removesuffix('_confidence')})"
    return None


def _registry_rejection_reason(data: dict) -> str | None:
    """Hard registry failures — REJECTED."""
    if not data.get("is_valid"):
        return "Tax code is not valid in the state registry"
    company = data.get("company") or {}
    status = company.get("business_status_en") or company.get("business_status") or ""
    if status and status.strip().lower() not in _ACTIVE_STATUSES:
        return f"Business is not active in the state registry ({status})"
    return None


def _cross_check_review_reason(ocr: dict, tax: dict) -> str | None:
    """Certificate ↔ registry cross-checks (integration guide §5).

    Mismatches and incomplete data here are MANUAL_REVIEW, not REJECTED:
    Vietnamese names/codes survive OCR with minor differences, and a human
    can adjudicate what strict string comparison cannot.
    """
    company = tax.get("company") or {}

    registry_tax_code = (company.get("tax_code") or "").strip()
    ocr_tax_code = (str(ocr.get("tax_code")) or "").strip()
    if registry_tax_code and registry_tax_code != ocr_tax_code:
        return "Tax code differs between the certificate and the registry"

    registry_name = _normalize_name(company.get("name"))
    if registry_name and _normalize_name(ocr.get("name")) != registry_name:
        return "Business name differs between the certificate and the registry"

    registry_rep = _normalize_name(company.get("representative"))
    ocr_reps = [
        _normalize_name(rep.get("name"))
        for rep in (ocr.get("representatives") or [])
        if rep.get("name")
    ]
    if not registry_rep or not ocr_reps:
        return "Legal representative details are incomplete"
    if registry_rep not in ocr_reps:
        return "Legal representative differs between the certificate and the registry"
    return None


async def _rep_match_rejection_reason(
    db: AsyncSession, user_id, ocr: dict
) -> str | None:
    """Rule 7 (flag-gated): the SME's KYC-verified person_number must appear
    among the certificate's legal representatives."""
    if not settings.GVERIFY_KYB_REQUIRE_REP_MATCH:
        return None

    result = await db.execute(
        select(GVerifyVerification.person_number)
        .where(
            GVerifyVerification.user_id == user_id,
            GVerifyVerification.status == STATUS_APPROVED,
        )
        .order_by(GVerifyVerification.created_at.desc())
    )
    person_number = result.scalars().first()
    if not person_number:
        return "Complete personal identity verification (KYC) first"

    rep_ids = {
        (rep.get("id_number") or "").strip()
        for rep in (ocr.get("representatives") or [])
    }
    if person_number.strip() not in rep_ids:
        return "Your verified identity is not listed as a legal representative of this business"
    return None


async def latest_for_user(db: AsyncSession, user_id) -> GVerifyKybVerification | None:
    result = await db.execute(
        select(GVerifyKybVerification)
        .where(GVerifyKybVerification.user_id == user_id)
        .order_by(GVerifyKybVerification.created_at.desc())
    )
    return result.scalars().first()


async def run_kyb_verification(
    db: AsyncSession,
    user: User,
    *,
    document_b64: str,
    document_type: str,
) -> GVerifyKybVerification:
    """Run the full one-shot KYB flow and return the terminal attempt row.

    Raises ImageValidationError (caller error, no row created) or
    client.GVerifyError (provider failure — the FAILED attempt row is flushed;
    the caller must commit so the failure is recorded).
    """
    if document_type not in DOCUMENT_TYPES:
        raise ImageValidationError(
            f"document_type must be one of {', '.join(DOCUMENT_TYPES)}"
        )
    raw, filename, content_type = _validate_document(document_b64)

    attempt = GVerifyKybVerification(
        user_id=user.id, status=STATUS_PENDING, document_type=document_type
    )
    db.add(attempt)
    await db.flush()

    # Retain the certificate under verification/KYB/<attempt-id>/ —
    # best-effort; the attempt proceeds even if storage is down.
    await storage.store_kyb_document(attempt.id, certificate=raw)

    try:
        ocr = await client.ocrx_decode(
            file_bytes=raw,
            filename=filename,
            content_type=content_type,
            document_type=document_type,
        )
    except client.GVerifyError as exc:
        attempt.status = STATUS_FAILED
        attempt.rejection_reason = str(exc)
        await db.flush()
        raise

    attempt.ocr_transaction_code = ocr.get("transaction_code")
    attempt.ocr_data = ocr
    attempt.tax_code = ocr.get("tax_code")
    attempt.business_name = ocr.get("name")
    attempt.business_type = ocr.get("business_type")
    attempt.company_address = ocr.get("company_address")
    attempt.date_of_establishment = ocr.get("date_of_establishment")
    # COMPANY certificates carry charter_capital; HOUSEHOLD ones business_capital.
    attempt.charter_capital = ocr.get("charter_capital") or ocr.get("business_capital")
    attempt.representatives = ocr.get("representatives")

    # Decision flow per the provider integration guide: hard OCR failures
    # reject; soft signals (low confidence) park for MANUAL_REVIEW — both
    # before the (billable) registry call.
    reason = _ocr_rejection_reason(ocr)
    if reason is None:
        reason = await _rep_match_rejection_reason(db, user.id, ocr)
    if reason is not None:
        attempt.status = STATUS_REJECTED
        attempt.rejection_reason = reason
        await db.flush()
        return attempt

    review = _ocr_review_reason(ocr)
    if review is not None:
        attempt.status = STATUS_MANUAL_REVIEW
        attempt.rejection_reason = review
        await db.flush()
        return attempt

    try:
        tax = await client.taxcode_verify(tax_code=str(ocr.get("tax_code")).strip())
    except client.GVerifyError as exc:
        attempt.status = STATUS_FAILED
        attempt.rejection_reason = str(exc)
        await db.flush()
        raise

    attempt.tax_transaction_code = tax.get("transaction_code")
    attempt.tax_data = tax

    reason = _registry_rejection_reason(tax)
    if reason is not None:
        attempt.status = STATUS_REJECTED
        attempt.rejection_reason = reason
    else:
        review = _cross_check_review_reason(ocr, tax)
        if review is not None:
            attempt.status = STATUS_MANUAL_REVIEW
            attempt.rejection_reason = review
        else:
            attempt.status = STATUS_APPROVED
    await db.flush()
    return attempt


def business_status(attempt: GVerifyKybVerification) -> str | None:
    """The registry's business status for an attempt, when the registry ran."""
    if not attempt.tax_data:
        return None
    company = attempt.tax_data.get("company") or {}
    return company.get("business_status_en") or company.get("business_status")
