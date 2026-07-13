from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class KycVerifyRequest(BaseModel):
    """Body for POST /gverify/kyc/verify.

    Images are base64 strings (JPEG or PNG, decoded size <= 10MB each),
    mirroring GVerify's own base64 endpoints.
    """

    id_front_b64: str
    id_back_b64: str
    portrait_b64: str


class KycVerifyResponse(BaseModel):
    """Synchronous verdict for a verification attempt (APPROVED or REJECTED)."""

    verification_id: UUID
    status: str
    is_approved: bool
    rejection_reason: str | None = None
    person_number: str | None = None
    full_name: str | None = None
    date_of_birth: str | None = None
    face_match_score: float | None = None
    created_at: datetime | None = None


class HandoffResponse(BaseModel):
    """Short-lived token for the phone capture flow (encoded in a QR)."""

    token: str
    expires_in_seconds: int


class KycStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_id: UUID
    status: str
    is_terminal: bool
    is_approved: bool
    rejection_reason: str | None = None
    person_number: str | None = None
    full_name: str | None = None
    updated_at: datetime | None = None
