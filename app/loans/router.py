from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.loans.schemas import LoanApplicationCreate, LoanApplicationOut
from app.loans.service import create_application, submit_application
from uuid import UUID

from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/loans", tags=["loans"])

require_sme = require_roles(Role.SME)


@router.post("/applications", response_model=LoanApplicationOut, status_code=201)
def create_loan_application(
    body: LoanApplicationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    row = create_application(db, body, current_user)
    append_audit(
        db,
        entity_type="LOAN_APPLICATION",
        entity_id=row.id,
        action="CREATE",
        actor_id=current_user.id,
        after_state={"project_id": str(row.project_id), "status": row.status},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return row


@router.post("/applications/{application_id}/submit", response_model=LoanApplicationOut)
def submit_loan_application(
    application_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    row = submit_application(db, application_id, current_user)
    append_audit(
        db,
        entity_type="LOAN_APPLICATION",
        entity_id=row.id,
        action="SUBMIT",
        actor_id=current_user.id,
        after_state={"status": row.status},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return row
