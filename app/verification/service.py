"""Verification business logic built on Didit's Sessions API.

Handles both KYC (individual identity, investors) and KYB (business
verification, SMEs); the two share this module and one table, and differ only
by the Didit workflow run and the `verification_type` stored.

Flow (https://docs.didit.me/sessions-api/overview):
  1. start_verification  -> create a Didit session, persist it, hand the URL to the FE
  2. user completes the flow in Didit's hosted UI
  3. Didit calls our webhook (handle_webhook) and/or the FE polls (sync_verification)
  4. we store the terminal status + full decision payload
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.users.models import User
from app.verification import client
from app.verification.models import Verification, VerificationWebhookEvent

# Reject webhooks whose timestamp is more than this many seconds from now
# (replay-attack defense, per Didit docs).
_WEBHOOK_MAX_SKEW_SECONDS = 300


def _callback_url() -> str | None:
    if settings.DIDIT_CALLBACK_URL:
        return settings.DIDIT_CALLBACK_URL
    if settings.FRONTEND_URL:
        return f"{settings.FRONTEND_URL.rstrip('/')}/kyc/callback"
    return None


def _normalize_language(value: str | None) -> str | None:
    """Reduce a frontend locale to an ISO 639-1 code Didit accepts.

    "vi" -> "vi", "vi-VN" -> "vi", "en_US" -> "en". Returns None if empty.
    """
    if not value:
        return None
    code = value.replace("_", "-").split("-")[0].strip().lower()
    return code or None


def _workflow_for(verification_type: str) -> str | None:
    """Select the Didit workflow id for a verification type (KYC vs KYB)."""
    if verification_type == "KYB":
        return settings.DIDIT_KYB_WORKFLOW_ID
    return settings.DIDIT_WORKFLOW_ID


def _latest_for_user(
    db: Session, user_id, verification_type: str
) -> Verification | None:
    return (
        db.query(Verification)
        .filter(
            Verification.user_id == user_id,
            Verification.verification_type == verification_type,
        )
        .order_by(Verification.created_at.desc())
        .first()
    )


def start_verification(
    db: Session,
    user: User,
    *,
    verification_type: str = "KYC",
    language: str | None = None,
) -> Verification:
    """Create (or reuse) a Didit session of the given type for the user.

    `verification_type` is "KYC" (individual identity, investors) or "KYB"
    (business verification, SMEs) and selects which Didit workflow to run.

    If the user already has a non-terminal verification of the same type we
    return it instead of creating a duplicate — this mirrors Didit's own
    vendor_data idempotency.

    `language` is the caller's preferred locale (e.g. from the frontend); it
    falls back to the DIDIT_LANGUAGE env default when not provided.
    """
    existing = _latest_for_user(db, user.id, verification_type)
    if existing is not None and not existing.is_terminal:
        return existing

    lang = _normalize_language(language) or _normalize_language(settings.DIDIT_LANGUAGE)
    contact = {"email": user.email} if user.email else None
    data = client.create_session(
        workflow_id=_workflow_for(verification_type),
        vendor_data=str(user.id),
        callback=_callback_url(),
        metadata={"user_id": str(user.id), "verification_type": verification_type},
        contact_details=contact,
        language=lang,
    )

    verification = Verification(
        user_id=user.id,
        verification_type=verification_type,
        session_id=str(data["session_id"]),
        session_number=data.get("session_number"),
        vendor_data=data.get("vendor_data") or str(user.id),
        workflow_id=str(data.get("workflow_id")) if data.get("workflow_id") else None,
        verification_url=data.get("url"),
        status=data.get("status") or "Not Started",
    )
    db.add(verification)
    db.flush()
    return verification


def sync_verification(db: Session, verification: Verification) -> Verification:
    """Pull the latest decision from Didit and persist status + decision."""
    data = client.retrieve_decision(verification.session_id)
    verification.status = data.get("status") or verification.status
    verification.decision = data
    db.add(verification)
    db.flush()
    return verification


def get_status(
    db: Session, user: User, verification_type: str = "KYC"
) -> Verification | None:
    return _latest_for_user(db, user.id, verification_type)


# --------------------------------------------------------------------------- #
# Webhook verification
# --------------------------------------------------------------------------- #
def _webhook_secret() -> str | None:
    # Prefer the spec's DIDIT_WEBHOOK_SECRET; accept the legacy name as a fallback.
    return settings.DIDIT_WEBHOOK_SECRET or settings.DIDIT_WEBHOOK_SECRET_KEY


def _shorten_floats(value):
    """Whole-number floats (1.0) -> ints (1), recursively.

    Python's json parser turns ``1.0`` into a float, which would re-serialise as
    ``"1.0"`` and break the HMAC. Didit's server canonicalisation emits ``"1"``,
    so we collapse integral floats to match. Mirrors the JS ``shortenFloats``.
    """
    if isinstance(value, list):
        return [_shorten_floats(v) for v in value]
    if isinstance(value, dict):
        return {k: _shorten_floats(v) for k, v in value.items()}
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _canonical_v2(parsed) -> str:
    """Reproduce Didit's X-Signature-V2 canonical form.

    shortenFloats -> recursive key sort -> compact JSON with unescaped Unicode.
    Equivalent to JS ``JSON.stringify(sortKeys(shortenFloats(parsed)))``.
    """
    return json.dumps(
        _shorten_floats(parsed),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def verify_webhook(raw_body: bytes, headers: dict[str, str]) -> bool:
    """Verify a Didit webhook delivery (HMAC-SHA256, constant-time compare).

    Didit ships three signature headers; we accept the delivery if any supported
    variant matches, after enforcing the 300s timestamp freshness window.
    Reference: https://docs.didit.me/integration/webhooks

      - X-Signature-V2     : HMAC over canonical JSON (recommended; primary here)
      - X-Signature        : HMAC over the exact raw request bytes
      - X-Signature-Simple : HMAC over "{timestamp}:{session_id}:{status}:{webhook_type}"
    """
    secret = _webhook_secret()
    if not secret:
        # Fail closed: without a configured secret we cannot trust the caller.
        return False

    # Header lookups are case-insensitive.
    lower = {k.lower(): v for k, v in headers.items()}
    timestamp = lower.get("x-timestamp")
    signature_v2 = lower.get("x-signature-v2")
    signature = lower.get("x-signature")
    signature_simple = lower.get("x-signature-simple")

    # Replay protection — required.
    if timestamp is None:
        return False
    try:
        if abs(int(time.time()) - int(timestamp)) > _WEBHOOK_MAX_SKEW_SECONDS:
            return False
    except (TypeError, ValueError):
        return False

    secret_bytes = secret.encode("utf-8")

    try:
        payload = json.loads(raw_body or b"{}")
    except json.JSONDecodeError:
        payload = None

    # Variant 1 (recommended): canonical V2 — survives middleware re-encoding.
    if signature_v2 and payload is not None:
        expected = hmac.new(
            secret_bytes, _canonical_v2(payload).encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(signature_v2, expected):
            return True

    # Variant 2: HMAC over the exact raw body bytes.
    if signature:
        expected = hmac.new(secret_bytes, raw_body, hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature, expected):
            return True

    # Variant 3: envelope-only fallback (does NOT authenticate `decision`).
    if signature_simple and payload is not None:
        canonical = (
            f"{timestamp}:{payload.get('session_id')}:"
            f"{payload.get('status')}:{payload.get('webhook_type')}"
        )
        expected = hmac.new(
            secret_bytes, canonical.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        if hmac.compare_digest(signature_simple, expected):
            return True

    return False


def already_processed(db: Session, event_id: str | None) -> bool:
    """True if this Didit delivery (event_id) was already applied.

    Didit redelivers on 5xx/404, so we dedupe on the per-delivery event_id to
    keep webhook handling idempotent.
    """
    if not event_id:
        return False
    return (
        db.query(VerificationWebhookEvent.event_id)
        .filter(VerificationWebhookEvent.event_id == event_id)
        .first()
        is not None
    )


def handle_webhook(db: Session, payload: dict[str, Any]) -> Verification | None:
    """Apply a verified webhook payload to the matching verification row.

    The webhook is treated as a trigger: we persist the envelope status and
    any embedded decision. (Media URLs in the decision are short-lived, so
    consumers that need fresh links should re-sync.)
    """
    session_id = str(payload.get("session_id")) if payload.get("session_id") else None
    if not session_id:
        return None

    # Record the delivery for idempotency before applying side effects.
    event_id = payload.get("event_id")
    if event_id:
        db.add(VerificationWebhookEvent(event_id=str(event_id), session_id=session_id))

    verification = (
        db.query(Verification)
        .filter(Verification.session_id == session_id)
        .first()
    )
    if verification is None:
        return None

    # Status strings are case-sensitive literals; store them verbatim.
    status = payload.get("status")
    if status:
        verification.status = status
    decision = payload.get("decision")
    if decision is not None:
        verification.decision = decision
    db.add(verification)
    db.flush()
    return verification
