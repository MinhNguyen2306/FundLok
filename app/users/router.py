from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.models import User
from app.users.schemas import (
    AvatarConfirmRequest,
    AvatarPresignRequest,
    AvatarPresignResponse,
    UserUpdateRequest,
)
from app.users.service import (
    confirm_avatar,
    create_avatar_presign,
    update_user_profile,
    user_me_payload,
)
from app.utils.audit import append_audit
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def read_current_user(current_user: User = Depends(get_current_user)):
    return user_me_payload(current_user)


@router.patch("/me")
def update_current_user(
    body: UserUpdateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    before = {
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "bio": current_user.bio,
    }
    user = update_user_profile(db, body, current_user)
    append_audit(
        db,
        entity_type="USER",
        entity_id=user.id,
        action="PROFILE_UPDATED",
        actor_id=user.id,
        before_state=before,
        after_state={"full_name": user.full_name, "phone": user.phone, "bio": user.bio},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return user_me_payload(user)


@router.post("/me/avatar/presign", response_model=AvatarPresignResponse, status_code=201)
def presign_avatar(
    body: AvatarPresignRequest,
    current_user: User = Depends(get_current_user),
):
    file_key, upload_url, expires_in = create_avatar_presign(body, current_user)
    return AvatarPresignResponse(
        file_key=file_key,
        upload_url=upload_url,
        expires_in=expires_in,
    )


@router.post("/me/avatar/confirm")
def confirm_avatar_upload(
    body: AvatarConfirmRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = confirm_avatar(db, body, current_user)
    append_audit(
        db,
        entity_type="USER",
        entity_id=user.id,
        action="AVATAR_UPDATED",
        actor_id=user.id,
        after_state={"avatar_key": user.avatar_key},
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    return user_me_payload(user)
