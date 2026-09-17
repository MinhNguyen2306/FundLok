"""Admin-restricted endpoints for the `documents` entity (T15, GAP-1).

Deliberately not under `app/admin/` (Phat's admin *panel* UI-facing module,
CLAUDE.md module ownership) or `app/uploads/` (Phat's UI-integrated upload
endpoints) -- this is the compliance write-path for the `Document` model
that already lives in `app/lending/models.py` alongside the
`project_has_verified_kyc` gate it feeds (`app/lending/kyc.py`). "Admin
endpoint" in the handoff describes who may call it (ADMIN role via RBAC),
not which router file it lives in.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.lending.schemas import DocumentApprovalCreate, DocumentOut
from app.lending.service import approve_document
from app.users.models import Role, User
from app.utils.rbac import require_roles

router = APIRouter(prefix="/lending", tags=["lending"])

require_admin = require_roles(Role.ADMIN)


@router.post("/documents/{document_id}/approve", response_model=DocumentOut, status_code=200)
async def post_approve_document(
    document_id: UUID,
    body: DocumentApprovalCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    document = await approve_document(
        db,
        document_id=document_id,
        rationale=body.rationale,
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    await db.refresh(document)
    return document
