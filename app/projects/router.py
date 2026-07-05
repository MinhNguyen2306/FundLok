from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.utils.jwt import get_current_user
from app.projects.schemas import (
    ProjectCreate,
    ProjectLoanApplicationOut,
    ProjectOut,
    ProjectWithApplicationOut,
)
from app.projects.service import (
    create_project,
    get_my_projects,
    display_projects,
)
from app.users.models import User


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectWithApplicationOut, status_code=201)
async def create_project_endpoint(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_project, loan_app = await create_project(db, project, current_user)
    out = ProjectWithApplicationOut.model_validate(new_project)
    if loan_app is not None:
        out.loan_application = ProjectLoanApplicationOut.model_validate(loan_app)
    await db.commit()
    return out


@router.get("", response_model=List[ProjectWithApplicationOut])
async def list_my_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    projects = await get_my_projects(db, current_user)
    results = []
    for project in projects:
        out = ProjectWithApplicationOut.model_validate(project)
        if project.loan_applications:
            out.loan_application = ProjectLoanApplicationOut.model_validate(
                project.loan_applications[0]
            )
        results.append(out)
    return results


@router.get("/public", response_model=List[ProjectOut])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await display_projects(db, current_user)
