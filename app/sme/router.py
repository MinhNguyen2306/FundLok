from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.projects.schemas import ProjectCreate, ProjectOut
from app.projects.service import create_project
from app.users.models import Role, User
from app.utils.audit import append_audit
from app.utils.rbac import require_roles

router = APIRouter(prefix="/sme", tags=["sme"])

require_sme = require_roles(Role.SME)


@router.post("/businesses", response_model=ProjectOut, status_code=201)
def create_business(
    body: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_sme),
):
    project, _loan_app = create_project(db, body, current_user)
    append_audit(
        db,
        entity_type="PROJECT",
        entity_id=project.id,
        action="CREATE_BUSINESS",
        actor_id=current_user.id,
        after_state={"legal_name": project.legal_name, "status": project.status},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return project
