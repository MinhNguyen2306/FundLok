from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.uploads.schemas import (
    FileCommitRequest,
    FileCommitResponse,
    FilePresignRequest,
    FilePresignResponse,
    LoanApplicationDocumentOut,
    UploadConfirmRequest,
    UploadConfirmResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from app.uploads.service import commit_file, confirm_uploads, create_file_presign, create_upload_presign
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.jwt import get_current_user
from app.utils.rbac import require_roles

router = APIRouter(prefix="/uploads", tags=["uploads"])

require_sme = require_roles(Role.SME)


@router.post("/init-upload", response_model=UploadPresignResponse, status_code=201)
async def presign_upload(
    body: UploadPresignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    doc, upload_url, expires_in = await create_upload_presign(db, body, current_user)
    append_audit(
        db,
        entity_type="LOAN_APPLICATION_DOCUMENT",
        entity_id=doc.id,
        action="UPLOAD_INITIATED",
        actor_id=current_user.id,
        after_state={
            "loan_application_id": str(doc.loan_application_id),
            "document_type": doc.document_type,
            "file_key": doc.file_key,
        },
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return UploadPresignResponse(
        document_id=doc.id,
        file_key=doc.file_key,
        upload_url=upload_url,
        expires_in=expires_in,
    )


@router.post("/confirm", response_model=UploadConfirmResponse)
async def confirm_upload(
    body: UploadConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    docs = await confirm_uploads(db, body, current_user)
    append_audit(
        db,
        entity_type="LOAN_APPLICATION",
        entity_id=body.loan_application_id,
        action="CONFIRM_UPLOADS",
        actor_id=current_user.id,
        after_state={"file_keys": [d.file_key for d in docs]},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return UploadConfirmResponse(
        documents=[LoanApplicationDocumentOut.model_validate(d) for d in docs]
    )


# --------------------------------------------------------------------------- #
# Generic (business/project-level) document presign+commit, merged in from
# app/files/ (HANDOFF-02 Fix C, module cleanup -- see docs/handoffs/HANDOFF-02-
# structural-fixes.md). Kept as its own router/prefix rather than folded into
# `router` above: route paths (/files/presign, /files/{file_id}/commit) and
# behavior are unchanged, since Phat confirmed the frontend doesn't currently
# call these, and whether this flow is planned-but-unbuilt or dead is still
# an open question with him -- this commit only relocates the code, it
# doesn't touch routes, schemas-on-the-wire, or behavior.
# --------------------------------------------------------------------------- #

files_router = APIRouter(prefix="/files", tags=["files"])


@files_router.post("/presign", response_model=FilePresignResponse, status_code=201)
async def presign(
    body: FilePresignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc, upload_url = await create_file_presign(db, body, current_user)
    append_audit(
        db,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="PRESIGN",
        actor_id=current_user.id,
        after_state={"purpose": doc.purpose, "business_id": str(body.business_id)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return FilePresignResponse(file_id=doc.id, upload_url=upload_url)


@files_router.post("/{file_id}/commit", response_model=FileCommitResponse)
async def commit(
    file_id: UUID,
    body: FileCommitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await commit_file(db, file_id, body, current_user)
    append_audit(
        db,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="COMMIT",
        actor_id=current_user.id,
        after_state={"status": doc.status, "checksum": body.checksum},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return FileCommitResponse(file_id=doc.id, status=doc.status)
