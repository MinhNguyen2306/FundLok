from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.lending.models import Project, ProjectOwnership
from app.projects.schemas import ProjectCreate
from app.users.models import Role, User


def create_project(db: Session, project_data: ProjectCreate, current_user: User):
    if current_user.role != Role.SME.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SMEs can create projects",
        )
    new_project = Project(**project_data.model_dump(), status="DRAFT")
    db.add(new_project)
    db.flush()
    db.add(
        ProjectOwnership(
            project_id=new_project.id,
            user_id=current_user.id,
            role="OWNER",
        )
    )
    db.flush()
    db.refresh(new_project)
    return new_project


def get_my_projects(db: Session, current_user: User):
    if current_user.role != Role.SME.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only SMEs can view their projects",
        )
    q = (
        db.query(Project)
        .join(ProjectOwnership)
        .filter(ProjectOwnership.user_id == current_user.id)
    )
    return q.all()


def user_owns_project(db: Session, user_id: UUID, project_id: UUID) -> bool:
    return (
        db.query(ProjectOwnership)
        .filter(
            ProjectOwnership.user_id == user_id,
            ProjectOwnership.project_id == project_id,
        )
        .first()
        is not None
    )
