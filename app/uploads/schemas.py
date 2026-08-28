import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

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


# --------------------------------------------------------------------------- #
# Generic (business/project-level) document presign+commit, merged in from
# app/files/ (HANDOFF-02 Fix C, module cleanup -- see docs/handoffs/HANDOFF-02-
# structural-fixes.md). Route paths and behavior are unchanged: still mounted
# under /files/*, kept as a separate schema set from the loan-application
# upload flow above since they model a different entity (Document, keyed by
# business_id/purpose) than LoanApplicationDocument.
# --------------------------------------------------------------------------- #

FILE_ALLOWED_MIME = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)
FILE_MAX_SIZE_BYTES = 25 * MB


class FilePresignRequest(BaseModel):
    business_id: UUID
    purpose: str
    # Bounded like UploadPresignRequest.filename above. Stored as given so the
    # UI can show the user their own filename; it is `safe_object_filename`d on
    # the way into the object key, which is where an unbounded raw value did
    # real damage. See that function for what and why.
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str

    @field_validator("mime_type")
    @classmethod
    def mime_allowlist(cls, v: str) -> str:
        if v not in FILE_ALLOWED_MIME:
            raise ValueError("mime_type not allowed")
        return v


# Characters allowed to survive into an object key. Everything else — path
# separators, control characters, URL metacharacters, non-ASCII — collapses to
# an underscore.
_SAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def safe_object_filename(raw: str) -> str:
    """Reduce a client filename to something safe to put in an object key.

    The generic presign builds its key as
    `fundlok/{business_id}/{uuid4}/{filename}` and then interpolates that key
    into a URL. A raw client value there is wrong on three counts:

    * `..` and `/` segments. S3/R2 treat keys as opaque strings so there is no
      filesystem traversal, but an HTTP client normalising `..` in the URL path
      before sending signs one key and writes another — at best a broken
      upload, at worst an object landing outside the intended prefix.
    * URL metacharacters (`?`, `#`, `&`, spaces) silently truncate or split the
      `?key=` query parameter the upload URL is built from.
    * Control characters, including CR/LF, which have no business in a key that
      may end up in a header or a log line.

    Keeping a readable, sanitised name is deliberate: the uuid4 segment already
    guarantees uniqueness, so the filename is only ever a human hint. The
    original, unmodified value is still stored in `Document.filename` for
    display — sanitising is about what reaches the KEY, not about losing the
    user's filename.
    """
    # Basename only: strip both separators, since a Windows client sends "\".
    name = raw.replace("\\", "/").rsplit("/", 1)[-1].strip()
    name = _SAFE_FILENAME_CHARS.sub("_", name)
    # A name that was entirely separators/dots ("..", "/", "") leaves nothing
    # usable; the uuid4 segment carries the identity, so a constant is fine.
    name = name.lstrip(".") or "upload"
    # Belt and braces: the 255 bound above applies to the raw input, and
    # sanitising never lengthens a name, but keep the key segment bounded
    # regardless of how this is called.
    return name[:255]


class FilePresignResponse(BaseModel):
    file_id: UUID
    upload_url: str


class FileCommitRequest(BaseModel):
    checksum: str
    size: int

    @field_validator("size")
    @classmethod
    def size_cap(cls, v: int) -> int:
        if v < 0 or v > FILE_MAX_SIZE_BYTES:
            raise ValueError("size out of allowed range")
        return v


class FileCommitResponse(BaseModel):
    file_id: UUID
    status: str
