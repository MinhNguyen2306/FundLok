from uuid import UUID

from pydantic import BaseModel, field_validator


ALLOWED_MIME = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)
MAX_SIZE_BYTES = 25 * 1024 * 1024


class PresignRequest(BaseModel):
    business_id: UUID
    purpose: str
    filename: str
    mime_type: str

    @field_validator("mime_type")
    @classmethod
    def mime_allowlist(cls, v: str) -> str:
        if v not in ALLOWED_MIME:
            raise ValueError("mime_type not allowed")
        return v


class PresignResponse(BaseModel):
    file_id: UUID
    upload_url: str


class CommitRequest(BaseModel):
    checksum: str
    size: int

    @field_validator("size")
    @classmethod
    def size_cap(cls, v: int) -> int:
        if v < 0 or v > MAX_SIZE_BYTES:
            raise ValueError("size out of allowed range")
        return v


class CommitResponse(BaseModel):
    file_id: UUID
    status: str
