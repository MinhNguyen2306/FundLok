from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.lending.models import LoanApplication
from app.loans.schemas import LoanApplicationCreate
from app.projects.service import user_owns_project
from app.users.models import Role, User
from uuid import UUID


async def create_application(db: AsyncSession, body: LoanApplicationCreate, current_user: User) -> LoanApplication:
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can create applications")
    if not await user_owns_project(db, current_user.id, body.business_id):
        raise HTTPException(status_code=403, detail="Business does not belong to this user")
    app_row = LoanApplication(
        project_id=body.business_id,
        requested_amount=body.requested_amount,
        purpose=body.purpose,
        repayment_preference=body.repayment_preference,
        status="DRAFT",
    )
    db.add(app_row)
    await db.flush()
    await db.refresh(app_row)
    return app_row


async def submit_application(db: AsyncSession, application_id: UUID, current_user: User) -> LoanApplication:
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can submit")
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == application_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    if not await user_owns_project(db, current_user.id, row.project_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    if row.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application is not in DRAFT status")
    row.status = "SUBMITTED"
    row.submitted_at = datetime.now(timezone.utc)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row
