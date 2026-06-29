"""Thin HTTP client for the Didit Verification API (Sessions API v3).

Docs: https://docs.didit.me/sessions-api/overview

The verification API authenticates with a long-lived secret on the
``x-api-key`` header (NOT OAuth bearer). Calls must originate server-side.
Both KYC (individual) and KYB (business) flows use this same client; they
differ only by the ``workflow_id`` passed to ``create_session``.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings


class DiditError(RuntimeError):
    """Raised when Didit returns a non-success response or is unreachable."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> dict[str, str]:
    if not settings.DIDIT_API_KEY:
        raise DiditError("DIDIT_API_KEY is not configured")
    return {
        "x-api-key": settings.DIDIT_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_session(
    *,
    workflow_id: str | None,
    vendor_data: str,
    callback: str | None = None,
    metadata: dict[str, Any] | None = None,
    contact_details: dict[str, Any] | None = None,
    language: str | None = None,
) -> dict[str, Any]:
    """POST /v3/session/ — create a verification session.

    ``workflow_id`` selects the Didit flow (KYC vs KYB). ``vendor_data`` is our
    stable per-user identifier; Didit uses it for duplicate detection (the same
    value returns an existing unfinished session instead of creating a new one).
    """
    if not workflow_id:
        raise DiditError("Didit workflow_id is not configured")

    payload: dict[str, Any] = {
        "workflow_id": workflow_id,
        "vendor_data": vendor_data,
    }
    if callback:
        payload["callback"] = callback
    if metadata:
        payload["metadata"] = metadata
    if contact_details:
        payload["contact_details"] = contact_details
    if language:
        payload["language"] = language

    url = f"{settings.DIDIT_BASE_URL.rstrip('/')}/v3/session/"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers=_headers())
    except httpx.RequestError as exc:
        raise DiditError(f"Could not reach Didit: {exc}") from exc

    if resp.status_code not in (200, 201):
        raise DiditError(
            f"Didit create_session failed ({resp.status_code}): {resp.text}",
            status_code=resp.status_code,
        )
    return resp.json()


def retrieve_decision(session_id: str) -> dict[str, Any]:
    """GET /v3/session/{session_id}/decision/ — full verification result."""
    url = f"{settings.DIDIT_BASE_URL.rstrip('/')}/v3/session/{session_id}/decision/"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=_headers())
    except httpx.RequestError as exc:
        raise DiditError(f"Could not reach Didit: {exc}") from exc

    if resp.status_code != 200:
        raise DiditError(
            f"Didit retrieve_decision failed ({resp.status_code}): {resp.text}",
            status_code=resp.status_code,
        )
    return resp.json()
