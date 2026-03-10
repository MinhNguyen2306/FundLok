from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils.jwt import get_current_user, oauth2_scheme
from app.users.models import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
def read_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status
    }