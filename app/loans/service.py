from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.lending.models import LoanApplication
from app.loans.schemas import LoanApplicationCreate, LoanApplicationFiguresIn
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


async def _owned_application(
    db: AsyncSession, application_id: UUID, current_user: User
) -> LoanApplication:
    """Load an application the caller is actually allowed to touch.

    404 rather than 403 when the application exists but belongs to someone
    else: telling a stranger "this exists but is not yours" confirms which
    application ids are real, which is an enumeration oracle over other SMEs'
    borrowing.
    """
    result = await db.execute(select(LoanApplication).where(LoanApplication.id == application_id))
    row = result.scalar_one_or_none()
    if not row or not await user_owns_project(db, current_user.id, row.project_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return row


async def save_figures(
    db: AsyncSession,
    application_id: UUID,
    body: LoanApplicationFiguresIn,
    current_user: User,
) -> LoanApplication:
    """Replace the self-reported figures on a draft application.

    A full replace, not a merge: the wizard always sends the complete set, and
    merging would let a second request that omitted a field silently keep a
    stale value the applicant believed they had cleared.
    """
    if current_user.role != Role.SME.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SMEs can save figures")

    row = await _owned_application(db, application_id, current_user)

    # Figures are underwriting inputs. Once the application is submitted they
    # are evidence of what was claimed, so they freeze with it -- otherwise an
    # applicant could restate their revenue after seeing the offer.
    if row.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Application is not in DRAFT status")

    row.self_reported_figures = body.model_dump()
    row.figures_updated_at = datetime.now(timezone.utc)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


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
