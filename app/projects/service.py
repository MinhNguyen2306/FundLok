from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.lending.models import LoanApplication, Project, ProjectOwnership
from app.projects.schemas import ProjectCreate
from app.users.models import Role, User


from sqlalchemy.exc import IntegrityError


async def create_project(
    db: AsyncSession, project_data: ProjectCreate, current_user: User
) -> tuple[Project, LoanApplication | None]:
    if current_user.role != Role.SME.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SMEs can create projects",
        )
    try:
        new_project = Project(
            **project_data.model_dump(exclude={"loan_application"}), status="DRAFT"
        )
        db.add(new_project)
        await db.flush()
        db.add(
            ProjectOwnership(
                project_id=new_project.id,
                user_id=current_user.id,
                role="OWNER",
            )
        )
        await db.flush()
        loan_app = None
        if project_data.loan_application is not None:
            loan_app = LoanApplication(
                project_id=new_project.id,
                requested_amount=project_data.loan_application.requested_amount,
                purpose=project_data.loan_application.purpose,
                repayment_preference=project_data.loan_application.repayment_preference,
                status="DRAFT",
            )
            db.add(loan_app)
            await db.flush()
            # Re-read with `documents` eagerly loaded. ProjectLoanApplicationOut
            # includes that relationship, and letting Pydantic read it unloaded
            # fires a lazy load during model_validate -- which on an
            # AsyncSession raises MissingGreenlet (IO outside the greenlet
            # context), a 500 on every create-with-loan request. Same reason
            # get_my_projects() uses selectinload. Loading it here also picks up
            # the server-side defaults (status, created_at) in one round trip,
            # so no separate refresh() is needed.
            # populate_existing: the row is already in the identity map, so
            # without it SQLAlchemy keeps the Python-side values and the create
            # response echoes the client's precision ("800000000") while
            # GET /projects reports what Postgres stored in Numeric(15,2)
            # ("800000000.00"). Reloading makes both endpoints agree and makes
            # the response describe the row as persisted.
            loan_app = (
                await db.execute(
                    select(LoanApplication)
                    .where(LoanApplication.id == loan_app.id)
                    .options(selectinload(LoanApplication.documents))
                    .execution_options(populate_existing=True)
                )
            ).scalar_one()
        await db.refresh(new_project)
        return new_project, loan_app
    except IntegrityError as e:
        await db.rollback()
        err_msg = str(e.orig)
        if "tax_id" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your bussiness tax ID is already associated with another project. Please contact support if you believe this is an error.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error: check unique fields or constraints."
        )


async def get_my_projects(db: AsyncSession, current_user: User):
    if current_user.role != Role.SME.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SMEs can view their projects",
        )
    result = await db.execute(
        select(Project)
        .join(ProjectOwnership)
        .where(ProjectOwnership.user_id == current_user.id)
        .options(
            selectinload(Project.loan_applications).selectinload(
                LoanApplication.documents
            )
        )
    )
    return result.scalars().all()


async def user_owns_project(db: AsyncSession, user_id: UUID, project_id: UUID) -> bool:
    result = await db.execute(
        select(ProjectOwnership).where(
            ProjectOwnership.user_id == user_id,
            ProjectOwnership.project_id == project_id,
        )
    )
    return result.scalar_one_or_none() is not None


async def display_projects(db: AsyncSession, current_user: User):
    if current_user.role != Role.INVESTOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investors can view projects",
        )
    result = await db.execute(select(Project).where(Project.status == "ACTIVE"))
    return result.scalars().all()
