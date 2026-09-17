from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.loans.schemas import (
    LoanApplicationCreate,
    LoanApplicationFiguresIn,
    LoanApplicationFiguresOut,
    LoanApplicationOut,
)
from app.loans.service import create_application, save_figures, submit_application
from uuid import UUID

from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/loans", tags=["loans"])

require_sme = require_roles(Role.SME)


@router.post("/applications", response_model=LoanApplicationOut, status_code=201)
async def create_loan_application(
    body: LoanApplicationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    row = await create_application(db, body, current_user)
    append_audit(
        db,
        entity_type="LOAN_APPLICATION",
        entity_id=row.id,
        action="CREATE",
        actor_id=current_user.id,
        after_state={"project_id": str(row.project_id), "status": row.status},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return row


@router.put(
    "/applications/{application_id}/figures",
    response_model=LoanApplicationFiguresOut,
)
async def save_loan_application_figures(
    application_id: UUID,
    body: LoanApplicationFiguresIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    """Store the figures the applicant typed on the revenue and costs steps.

    PUT rather than PATCH: the wizard owns the whole set and replaces it each
    time, so the request is idempotent and a retry after a dropped connection
    cannot half-apply.
    """
    row = await save_figures(db, application_id, body, current_user)

    # The figures themselves stay out of the audit trail -- they are the
    # applicant's commercial data, and the row already holds them. What matters
    # for an audit is that they changed, by whom, and when.
    append_audit(
        db,
        entity_type="LOAN_APPLICATION",
        entity_id=row.id,
        action="SAVE_FIGURES",
        actor_id=current_user.id,
        after_state={"figures_updated_at": row.figures_updated_at.isoformat()},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return LoanApplicationFiguresOut(
        **row.self_reported_figures,
        figures_updated_at=row.figures_updated_at,
    )


@router.post("/applications/{application_id}/submit", response_model=LoanApplicationOut)
async def submit_loan_application(
    application_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    row = await submit_application(db, application_id, current_user)
    append_audit(
        db,
        entity_type="LOAN_APPLICATION",
        entity_id=row.id,
        action="SUBMIT",
        actor_id=current_user.id,
        after_state={"status": row.status},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return row
