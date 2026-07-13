"""Async HTTP client for the GVerify / GHub eKYC API (Datatrust, v2.5.1).

Spec: docs/specs/gverify/ekyc-kyc-verification.md

We use the base64 JSON variants of the endpoints (not the multipart ones) so
the whole request/response cycle stays JSON. Every endpoint shares one
envelope: ``{success, error{code, message}, data{...}}`` — ``success=false``
or a non-200 HTTP status is a provider error and raises GVerifyError.

Auth is a long-lived key on the ``x-api-key`` header plus a partner ``code``
in the JSON body; calls must originate server-side.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

_TIMEOUT = 30.0  # OCR + biometric calls are slower than plain CRUD


class GVerifyError(RuntimeError):
    """Raised when GVerify returns a non-success response or is unreachable."""

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


def _headers() -> dict[str, str]:
    if not settings.GVERIFY_API_KEY:
        raise GVerifyError("GVERIFY_API_KEY is not configured")
    return {
        "x-api-key": settings.GVERIFY_API_KEY,
        "os-type": settings.GVERIFY_OS_TYPE,
        "Content-Type": "application/json",
        "Accept": "*/*",
    }


async def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST to GVerify and unwrap the {success, error, data} envelope."""
    if not settings.GVERIFY_BASE_URL:
        raise GVerifyError("GVERIFY_BASE_URL is not configured")
    if not settings.GVERIFY_PARTNER_CODE:
        raise GVerifyError("GVERIFY_PARTNER_CODE is not configured")

    body = {"code": settings.GVERIFY_PARTNER_CODE, **payload}
    url = f"{settings.GVERIFY_BASE_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=_headers())
    except httpx.RequestError as exc:
        raise GVerifyError(f"Could not reach GVerify: {exc}") from exc

    if resp.status_code != 200:
        raise GVerifyError(
            f"GVerify {path} failed ({resp.status_code})",
            status_code=resp.status_code,
        )

    envelope = resp.json()
    if not envelope.get("success"):
        error = envelope.get("error") or {}
        raise GVerifyError(
            f"GVerify {path} returned an error: {error.get('message') or 'unknown'}",
            code=str(error.get("code")) if error.get("code") is not None else None,
            status_code=resp.status_code,
        )
    return envelope.get("data") or {}


async def verify_ocr_id(*, img_front_b64: str, img_back_b64: str) -> dict[str, Any]:
    """POST /ekyc/api/base64/verify-ocrid — OCR both faces of a CCCD/CMND.

    Returns the ``data`` object: extracted identity fields, per-field
    confidence scores, and front/back validity flags.
    """
    return await _post(
        "/ekyc/api/base64/verify-ocrid",
        {"img_front": img_front_b64, "img_back": img_back_b64},
    )


async def face_match(*, img1_b64: str, img2_b64: str) -> dict[str, Any]:
    """POST /ekyc/api/base64/face-match — 1:1 face comparison.

    Returns the ``data`` object: ``is_matching`` plus ``match`` (0–1 score).
    """
    return await _post(
        "/ekyc/api/base64/face-match",
        {"img1": img1_b64, "img2": img2_b64},
    )
