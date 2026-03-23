from datetime import datetime, timezone

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.lending.models import LoanApplication
from app.loans.schemas import LoanApplicationCreate
from app.projects.service import user_owns_project
from app.users.models import Role, User
from uuid import UUID


def create_application(db: Session, body: LoanApplicationCreate, current_user: User) -> LoanApplication:
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can create applications")
    if not user_owns_project(db, current_user.id, body.business_id):
        raise HTTPException(status_code=403, detail="Business does not belong to this user")
    app_row = LoanApplication(
        project_id=body.business_id,
        requested_amount=body.requested_amount,
        purpose=body.purpose,
        repayment_preference=body.repayment_preference,
        status="DRAFT",
    )
    db.add(app_row)
    db.flush()
    db.refresh(app_row)
    return app_row


def submit_application(db: Session, application_id: UUID, current_user: User) -> LoanApplication:
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can submit")
    row = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    if not user_owns_project(db, current_user.id, row.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    if row.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application is not in DRAFT status")
    row.status = "SUBMITTED"
    row.submitted_at = datetime.now(timezone.utc)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row
