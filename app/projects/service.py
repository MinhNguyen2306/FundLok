from sqlalchemy.orm import Session
from app.projects.models import Project
from app.projects.schemas import ProjectCreate
from app.users.models import User

def create_project(db: Session, project_data: ProjectCreate, current_user: User):
    if current_user.role != "SME":
        raise HTTPException(status_code=403, detail="Only SMEs can create projects")

    new_project = Project(**project_data.dict())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

def get_my_projects(db: Session, current_user: User):
    # For now, just list all projects (we'll filter by ownership later)
    return db.query(Project).all()