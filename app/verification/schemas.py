from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StartRequest(BaseModel):
    """Optional body for POST /{kyc,kyb}/start.

    `language` is the end user's locale from the frontend (e.g. "vi", "vi-VN",
    "en"). It is normalized to ISO 639-1 server-side; if omitted, the
    DIDIT_LANGUAGE default is used.
    """

    language: str | None = None


class StartResponse(BaseModel):
    """Returned when a verification session is created (or reused)."""

    verification_id: UUID
    session_id: str
    status: str
    verification_url: str | None = None


class StatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_id: UUID
    session_id: str
    status: str
    verification_type: str
    is_terminal: bool
    is_approved: bool
    verification_url: str | None = None
    updated_at: datetime | None = None


class DiditWebhookPayload(BaseModel):
    """Loose model for the Didit webhook body. We keep it permissive because
    Didit's `decision` shape evolves; only the envelope fields are required."""

    model_config = ConfigDict(extra="allow")

    event_id: str | None = None  # unique per delivery attempt — used for idempotency
    session_id: str
    status: str
    webhook_type: str | None = None
    timestamp: int | None = None
    vendor_data: str | None = None
    decision: dict[str, Any] | None = None
    resubmit_info: dict[str, Any] | None = None  # present when status == "Resubmitted"
