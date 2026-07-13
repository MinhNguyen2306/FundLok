"""Retention of verification documents in R2.

Every KYC/KYB attempt's submitted documents are stored under a deterministic
prefix keyed by the attempt id, so the evidence for any verdict (including
FAILED attempts) can be located without a DB column:

    {R2_VERIFICATION_BUCKET or R2_BUCKET}/
        verification/KYC/{verification_id}/id_front.{jpg|png}
        verification/KYC/{verification_id}/id_back.{jpg|png}
        verification/KYC/{verification_id}/portrait.{jpg|png}
        verification/KYB/{verification_id}/certificate.{jpg|png|pdf}

Uploads are best-effort: a storage outage must never block or fail the
verification itself (the provider payloads in Postgres remain the primary
audit record). Failures are logged and swallowed. boto3 is sync, so uploads
run in a worker thread to keep the event loop free.
"""
from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.utils import r2

logger = logging.getLogger(__name__)

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_PDF_MAGIC = b"%PDF"


def _bucket() -> str | None:
    return settings.R2_VERIFICATION_BUCKET or settings.R2_BUCKET


def _ext_and_type(raw: bytes) -> tuple[str, str]:
    if raw.startswith(_PNG_MAGIC):
        return "png", "image/png"
    if raw.startswith(_PDF_MAGIC):
        return "pdf", "application/pdf"
    # Callers validate magic bytes before we get here; JPEG is the default.
    return "jpg", "image/jpeg"


def _put(key: str, raw: bytes) -> None:
    _, content_type = _ext_and_type(raw)
    r2.put_bytes(key, raw, content_type, bucket=_bucket())


async def _store(kind: str, verification_id, documents: dict[str, bytes]) -> None:
    if not r2.is_configured():
        logger.warning(
            "R2 not configured — %s documents for %s not retained", kind, verification_id
        )
        return
    try:
        for name, raw in documents.items():
            ext, _ = _ext_and_type(raw)
            key = f"verification/{kind}/{verification_id}/{name}.{ext}"
            await asyncio.to_thread(_put, key, raw)
    except Exception:  # noqa: BLE001 — retention must never break verification
        logger.exception(
            "Failed to store %s verification documents for %s", kind, verification_id
        )


async def store_kyc_documents(
    verification_id, *, id_front: bytes, id_back: bytes, portrait: bytes
) -> None:
    await _store(
        "KYC",
        verification_id,
        {"id_front": id_front, "id_back": id_back, "portrait": portrait},
    )


async def store_kyb_document(verification_id, *, certificate: bytes) -> None:
    await _store("KYB", verification_id, {"certificate": certificate})
