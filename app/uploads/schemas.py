from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

MB = 1024 * 1024

# Per-wizard-step rules: allowed extensions and max size per document type.
# Step 1 (Hồ sơ pháp lý) produces two rows: legal_charter + business_registration.
DOCUMENT_TYPE_RULES: dict[str, dict] = {
    "legal_charter": {"extensions": {"pdf"}, "max_size": 25 * MB},
    "business_registration": {"extensions": {"pdf"}, "max_size": 25 * MB},
    "vat_tax_zip": {"extensions": {"zip"}, "max_size": 200 * MB},
    "financial_report": {"extensions": {"pdf"}, "max_size": 25 * MB},
    "e_invoice_data": {"extensions": {"zip", "xlsx", "csv", "xml"}, "max_size": 100 * MB},
    "cic_report": {"extensions": {"pdf"}, "max_size": 25 * MB},
}

EXTENSION_CONTENT_TYPES: dict[str, frozenset[str]] = {
    "pdf": frozenset({"application/pdf"}),
    "zip": frozenset({"application/zip", "application/x-zip-compressed"}),
    "xlsx": frozenset({"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}),
    "csv": frozenset({"text/csv"}),
    "xml": frozenset({"application/xml", "text/xml"}),
}


class UploadPresignRequest(BaseModel):
    loan_application_id: UUID
    document_type: str
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    size: int = Field(gt=0)


class UploadPresignResponse(BaseModel):
    document_id: UUID
    file_key: str
    upload_url: str
    expires_in: int


class UploadConfirmRequest(BaseModel):
    loan_application_id: UUID
    file_keys: list[str] = Field(min_length=1, max_length=20)


class LoanApplicationDocumentOut(BaseModel):
    id: UUID
    loan_application_id: UUID
    document_type: str
    file_key: str
    original_filename: str
    content_type: str | None
    file_size_bytes: int | None
    status: str
    uploaded_at: datetime | None

    model_config = {"from_attributes": True}


class UploadConfirmResponse(BaseModel):
    documents: list[LoanApplicationDocumentOut]
