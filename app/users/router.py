from fastapi import APIRouter, Depends

from app.utils.jwt import get_current_user
from app.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "status": current_user.status,
        "email_verified": current_user.email_verified
    }