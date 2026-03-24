from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.files.schemas import CommitRequest, CommitResponse, PresignRequest, PresignResponse
from app.files.service import commit_file, create_presign
from app.users.models import User
from app.utils.audit import append_audit
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/presign", response_model=PresignResponse, status_code=201)
def presign(
    body: PresignRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc, upload_url = create_presign(db, body, current_user)
    append_audit(
        db,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="PRESIGN",
        actor_id=current_user.id,
        after_state={"purpose": doc.purpose, "business_id": str(body.business_id)},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return PresignResponse(file_id=doc.id, upload_url=upload_url)


@router.post("/{file_id}/commit", response_model=CommitResponse)
def commit(
    file_id: UUID,
    body: CommitRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = commit_file(db, file_id, body, current_user)
    append_audit(
        db,
        entity_type="DOCUMENT",
        entity_id=doc.id,
        action="COMMIT",
        actor_id=current_user.id,
        after_state={"status": doc.status, "checksum": body.checksum},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return CommitResponse(file_id=doc.id, status=doc.status)
