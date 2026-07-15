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


def _headers(*, json_body: bool = True) -> dict[str, str]:
    if not settings.GVERIFY_API_KEY:
        raise GVerifyError("GVERIFY_API_KEY is not configured")
    headers = {
        "x-api-key": settings.GVERIFY_API_KEY,
        "os-type": settings.GVERIFY_OS_TYPE,
        "Accept": "*/*",
    }
    # For multipart requests httpx must set its own boundary Content-Type.
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _base_url() -> str:
    if not settings.GVERIFY_BASE_URL:
        raise GVerifyError("GVERIFY_BASE_URL is not configured")
    if not settings.GVERIFY_PARTNER_CODE:
        raise GVerifyError("GVERIFY_PARTNER_CODE is not configured")
    return settings.GVERIFY_BASE_URL.rstrip("/")


def _unwrap(resp: httpx.Response, path: str) -> dict[str, Any]:
    """Unwrap the {success, error, data} envelope shared by every endpoint."""
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


async def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """POST JSON to GVerify (partner code travels in the body)."""
    url = f"{_base_url()}{path}"
    body = {"code": settings.GVERIFY_PARTNER_CODE, **payload}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=body, headers=_headers())
    except httpx.RequestError as exc:
        raise GVerifyError(f"Could not reach GVerify: {exc}") from exc
    return _unwrap(resp, path)


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

    Call with ``img1`` = ID-card front, ``img2`` = live portrait (order per
    partner testing). Returns the ``data`` object: ``is_matching`` (the
    verdict), ``match`` (its "1"/"0" mirror) and ``matching`` (similarity %).
    """
    return await _post(
        "/ekyc/api/base64/face-match",
        {"img1": img1_b64, "img2": img2_b64},
    )


async def ocrx_decode(
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str,
    document_type: str,
) -> dict[str, Any]:
    """POST /ekyb/api/ocrx/decode — OCR a business registration certificate.

    This endpoint has no base64 variant: it takes multipart form-data
    (``file`` + ``type``), and — unlike the eKYC base64 endpoints — the
    partner ``code`` travels as a HEADER here, per the API doc.
    ``document_type`` is COMPANY | COMPANY_BRANCH | HOUSEHOLD.
    """
    path = "/ekyb/api/ocrx/decode"
    url = f"{_base_url()}{path}"
    headers = _headers(json_body=False)
    headers["code"] = settings.GVERIFY_PARTNER_CODE or ""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                url,
                files={"file": (filename, file_bytes, content_type)},
                data={"type": document_type},
                headers=headers,
            )
    except httpx.RequestError as exc:
        raise GVerifyError(f"Could not reach GVerify: {exc}") from exc
    return _unwrap(resp, path)


async def taxcode_verify(*, tax_code: str) -> dict[str, Any]:
    """POST /ekyb/api/taxcode/verify — check a tax code against the state
    registry (Tổng Cục Thuế). Returns ``is_valid`` plus the registered
    ``company`` profile (name, address, business_status, representative)."""
    return await _post(
        "/ekyb/api/taxcode/verify",
        {"ID": tax_code, "tax_type": "COMPANY"},
    )
