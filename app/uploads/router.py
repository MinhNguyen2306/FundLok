from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.uploads.schemas import (
    LoanApplicationDocumentOut,
    UploadConfirmRequest,
    UploadConfirmResponse,
    UploadPresignRequest,
    UploadPresignResponse,
)
from app.uploads.service import confirm_uploads, create_upload_presign
from app.users.models import Role, User
from app.utils.audit import append_audit
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
