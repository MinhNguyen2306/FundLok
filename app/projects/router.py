from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.utils.jwt import get_current_user
from app.projects.schemas import ProjectCreate, ProjectOut
from app.projects.service import create_project, get_my_projects
from app.users.models import User


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project_endpoint(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    out = create_project(db, project, current_user)
    db.commit()
    return out


@router.get("/", response_model=List[ProjectOut])
def list_my_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_my_projects(db, current_user)
