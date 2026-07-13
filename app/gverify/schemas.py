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


class KybRepresentative(BaseModel):
    """Slimmed legal-representative entry from the OCR X payload."""

    name: str | None = None
    id_number: str | None = None
    title: str | None = None


class KybVerifyRequest(BaseModel):
    """Body for POST /gverify/kyb/verify.

    The business registration certificate as base64 (JPEG, PNG or PDF,
    decoded size <= 10MB). document_type selects the OCR X variant:
    COMPANY | COMPANY_BRANCH | HOUSEHOLD (validated in the service so an
    unknown value returns the spec'd 400, not a 422).
    """

    document_b64: str
    document_type: str


class KybVerifyResponse(BaseModel):
    """Synchronous verdict for a KYB attempt (APPROVED or REJECTED)."""

    verification_id: UUID
    status: str
    is_approved: bool
    rejection_reason: str | None = None
    tax_code: str | None = None
    business_name: str | None = None
    business_type: str | None = None
    business_status: str | None = None  # from the tax registry, when reached
    representatives: list[KybRepresentative] = []
    created_at: datetime | None = None


class KybStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    verification_id: UUID
    status: str
    is_terminal: bool
    is_approved: bool
    rejection_reason: str | None = None
    tax_code: str | None = None
    business_name: str | None = None
    updated_at: datetime | None = None
