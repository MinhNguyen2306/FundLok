import uuid
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.lending.models import Document, Project
from app.files.schemas import CommitRequest, PresignRequest
from app.projects.service import user_owns_project
from app.users.models import Role, User


def _purpose_allowed(purpose: str) -> bool:
    return purpose in (
        "KYC_ID",
        "KYC_ADDRESS",
        "KYC_BUSINESS_REG",
        "BANK_STATEMENT",
        "INVOICE",
        "OTHER",
    )


def create_presign(
    db: Session,
    body: PresignRequest,
    current_user: User,
) -> tuple[Document, str]:
    if current_user.role not in (Role.SME.value, Role.ADMIN.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if not _purpose_allowed(body.purpose):
        raise HTTPException(status_code=400, detail="Invalid purpose")
    proj = db.query(Project).filter(Project.id == body.business_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role == Role.SME.value and not user_owns_project(db, current_user.id, body.business_id):
        raise HTTPException(status_code=403, detail="Business does not belong to this user")

    storage_key = f"fundlok/{body.business_id}/{uuid.uuid4()}/{body.filename}"
    doc = Document(
        entity_type="PROJECT",
        entity_id=body.business_id,
        purpose=body.purpose,
        filename=body.filename,
        mime_type=body.mime_type,
        status="PENDING",
        storage_key=storage_key,
    )
    db.add(doc)
    db.flush()
    upload_url = f"{settings.MOCK_UPLOAD_BASE_URL.rstrip('/')}/{doc.id}?key={storage_key}"
    return doc, upload_url


def commit_file(
    db: Session,
    file_id: UUID,
    body: CommitRequest,
    current_user: User,
) -> Document:
    doc = db.query(Document).filter(Document.id == file_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    if doc.entity_type == "PROJECT":
        if current_user.role == Role.SME.value and not user_owns_project(
            db, current_user.id, doc.entity_id
        ):
            raise HTTPException(status_code=403, detail="Not authorized")
        elif current_user.role not in (Role.SME.value, Role.ADMIN.value):
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        if current_user.role not in (Role.SME.value, Role.ADMIN.value):
            raise HTTPException(status_code=403, detail="Not authorized")

    if doc.status in ("APPROVED", "UPLOADED", "SCANNING") and doc.checksum_sha256 == body.checksum:
        return doc

    doc.checksum_sha256 = body.checksum
    doc.size_bytes = body.size
    doc.status = "SCANNING"
    db.add(doc)
    return doc
