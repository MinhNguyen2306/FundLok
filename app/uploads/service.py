import uuid
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.lending.models import Document, LoanApplication, LoanApplicationDocument, Project
from app.projects.service import user_owns_project
from app.uploads.schemas import (
    DOCUMENT_TYPE_RULES,
    EXTENSION_CONTENT_TYPES,
    FileCommitRequest,
    FilePresignRequest,
    UploadConfirmRequest,
    UploadPresignRequest,
)
from app.users.models import Role, User
from app.utils.r2 import delete_object, head_object, presign_put


async def _get_owned_draft_application(db: AsyncSession, application_id: UUID, current_user: User) -> LoanApplication:
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == application_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    if not await user_owns_project(db, current_user.id, row.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    if row.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application is not in DRAFT status")
    return row


def _validate_file(body: UploadPresignRequest) -> str:
    rules = DOCUMENT_TYPE_RULES.get(body.document_type)
    if rules is None:
        raise HTTPException(status_code=400, detail="Invalid document_type")
    if "." not in body.filename:
        raise HTTPException(status_code=400, detail="Filename must have an extension")
    ext = body.filename.rsplit(".", 1)[1].lower()
    if ext not in rules["extensions"]:
        allowed = ", ".join(sorted(rules["extensions"]))
        raise HTTPException(
            status_code=400,
            detail=f"Extension .{ext} not allowed for {body.document_type} (allowed: {allowed})",
        )
    if body.content_type not in EXTENSION_CONTENT_TYPES[ext]:
        raise HTTPException(status_code=400, detail=f"content_type not allowed for .{ext}")
    if body.size > rules["max_size"]:
        raise HTTPException(
            status_code=400,
            detail=f"File too large for {body.document_type} (max {rules['max_size']} bytes)",
        )
    return ext


async def create_upload_presign(
    db: AsyncSession,
    body: UploadPresignRequest,
    current_user: User,
) -> tuple[LoanApplicationDocument, str, int]:
    app_row = await _get_owned_draft_application(db, body.loan_application_id, current_user)
    ext = _validate_file(body)

    # Key is generated server-side; the client never picks it. The name is
    # deterministic per document type, so a re-upload overwrites the old object
    # and each application holds at most one file per type.
    file_key = f"application_documents/{current_user.id}/{app_row.id}/{body.document_type}.{ext}"
    result = await db.execute(
        select(LoanApplicationDocument).where(
            LoanApplicationDocument.loan_application_id == app_row.id,
            LoanApplicationDocument.document_type == body.document_type,
        )
    )
    doc = result.scalar_one_or_none()
    if doc:
        if doc.file_key != file_key:
            # Extension changed (e.g. e_invoice_data .zip -> .xlsx): the old
            # object would be orphaned, so remove it.
            delete_object(doc.file_key)
            doc.file_key = file_key
        doc.original_filename = body.filename
        doc.content_type = body.content_type
        doc.file_size_bytes = body.size
        doc.status = "PENDING"
        doc.uploaded_at = None
    else:
        doc = LoanApplicationDocument(
            loan_application_id=app_row.id,
            document_type=body.document_type,
            file_key=file_key,
            original_filename=body.filename,
            content_type=body.content_type,
            file_size_bytes=body.size,
            status="PENDING",
        )
        db.add(doc)
    await db.flush()
    upload_url = presign_put(file_key, body.content_type)
    return doc, upload_url, settings.R2_PRESIGN_EXPIRE_SECONDS


async def confirm_uploads(
    db: AsyncSession,
    body: UploadConfirmRequest,
    current_user: User,
) -> list[LoanApplicationDocument]:
    app_row = await _get_owned_draft_application(db, body.loan_application_id, current_user)

    file_keys = list(dict.fromkeys(body.file_keys))
    result = await db.execute(
        select(LoanApplicationDocument).where(
            LoanApplicationDocument.loan_application_id == app_row.id,
            LoanApplicationDocument.file_key.in_(file_keys),
        )
    )
    docs = result.scalars().all()
    by_key = {d.file_key: d for d in docs}
    missing = [k for k in file_keys if k not in by_key]
    if missing:
        raise HTTPException(status_code=400, detail=f"Unknown file_key(s): {', '.join(missing)}")

    now = datetime.now(timezone.utc)
    for key in file_keys:
        doc = by_key[key]
        if doc.status == "UPLOADED":
            continue
        head = head_object(key)
        if head is None:
            raise HTTPException(status_code=400, detail=f"Object not found in storage: {key}")
        max_size = DOCUMENT_TYPE_RULES[doc.document_type]["max_size"]
        if head["size"] and head["size"] > max_size:
            raise HTTPException(status_code=400, detail=f"Uploaded object too large: {key}")
        doc.file_size_bytes = head["size"]
        if head["content_type"]:
            doc.content_type = head["content_type"]
        doc.status = "UPLOADED"
        doc.uploaded_at = now
        db.add(doc)
    await db.flush()
    return [by_key[k] for k in file_keys]


# --------------------------------------------------------------------------- #
# Generic (business/project-level) document presign+commit, merged in from
# app/files/ (HANDOFF-02 Fix C, module cleanup). Behavior is unchanged from
# the original app/files/service.py -- only the import location moved.
# --------------------------------------------------------------------------- #

def _file_purpose_allowed(purpose: str) -> bool:
    return purpose in (
        "KYC_ID",
        "KYC_ADDRESS",
        "KYC_BUSINESS_REG",
        "BANK_STATEMENT",
        "INVOICE",
        "OTHER",
    )


async def create_file_presign(
    db: AsyncSession,
    body: FilePresignRequest,
    current_user: User,
) -> tuple[Document, str]:
    if current_user.role not in (Role.SME.value, Role.ADMIN.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if not _file_purpose_allowed(body.purpose):
        raise HTTPException(status_code=400, detail="Invalid purpose")
    result = await db.execute(select(Project).where(Project.id == body.business_id))
    proj = result.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Business not found")
    if current_user.role == Role.SME.value and not await user_owns_project(db, current_user.id, body.business_id):
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
    await db.flush()
    upload_url = f"{settings.MOCK_UPLOAD_BASE_URL.rstrip('/')}/{doc.id}?key={storage_key}"
    return doc, upload_url


async def commit_file(
    db: AsyncSession,
    file_id: UUID,
    body: FileCommitRequest,
    current_user: User,
) -> Document:
    result = await db.execute(select(Document).where(Document.id == file_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
    if doc.entity_type == "PROJECT":
        if current_user.role == Role.SME.value and not await user_owns_project(
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
