from uuid import UUID

from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status

from app.lending.models import LoanApplication, Project, ProjectOwnership
from app.projects.schemas import ProjectCreate
from app.users.models import Role, User


from sqlalchemy.exc import IntegrityError


def create_project(
    db: Session, project_data: ProjectCreate, current_user: User
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
        db.flush()
        db.add(
            ProjectOwnership(
                project_id=new_project.id,
                user_id=current_user.id,
                role="OWNER",
            )
        )
        db.flush()
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
            db.flush()
            db.refresh(loan_app)
        db.refresh(new_project)
        return new_project, loan_app
    except IntegrityError as e:
        db.rollback()
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
        .options(
            selectinload(Project.loan_applications).selectinload(
                LoanApplication.documents
            )
        )
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


def display_projects(db: Session, current_user: User):
    if current_user.role != Role.INVESTOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only investors can view projects",
        )
    return db.query(Project).filter(Project.status == "ACTIVE").all()