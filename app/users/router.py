from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.users.models import User
from app.users.schemas import (
    AvatarConfirmRequest,
    AvatarPresignRequest,
    AvatarPresignResponse,
    RoleSelectRequest,
    SetPasswordRequest,
    UserUpdateRequest,
)
from app.users.service import (
    confirm_avatar,
    create_avatar_presign,
    select_user_role,
    set_password,
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
async def update_current_user(
    body: UserUpdateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    before = {
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "bio": current_user.bio,
    }
    user = await update_user_profile(db, body, current_user)
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
    await db.commit()
    return user_me_payload(user)


@router.post("/me/password", status_code=200)
async def set_current_user_password(
    body: SetPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Set a first password on an account that doesn't have one.

    Changing an existing password is NOT done here -- that's forgot-password /
    reset-password, where the emailed token proves the mailbox.

    Currently unreachable in practice: `users.password_hash` is NOT NULL and
    /auth/register always sets it, so every account 400s. Two things make it
    live: a migration making `password_hash` nullable, and an OAuth sign-in
    endpoint that creates accounts without one (the frontend already calls
    /auth/oauth/login, which this API does not implement yet).
    """
    await set_password(db, body, current_user, background_tasks)
    append_audit(
        db,
        entity_type="USER",
        entity_id=current_user.id,
        action="PASSWORD_SET",
        actor_id=current_user.id,
        before_state={"has_password": False},
        after_state={"has_password": True},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"status": "success", "message": "Password set successfully"}


@router.patch("/me/role")
async def select_role(
    body: RoleSelectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    before = {"role": current_user.role}
    user = await select_user_role(db, body.role, current_user)
    append_audit(
        db,
        entity_type="USER",
        entity_id=user.id,
        action="ROLE_SELECTED",
        actor_id=user.id,
        before_state=before,
        after_state={"role": user.role},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
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
async def confirm_avatar_upload(
    body: AvatarConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = await confirm_avatar(db, body, current_user)
    append_audit(
        db,
        entity_type="USER",
        entity_id=user.id,
        action="AVATAR_UPDATED",
        actor_id=user.id,
        after_state={"avatar_key": user.avatar_key},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return user_me_payload(user)
