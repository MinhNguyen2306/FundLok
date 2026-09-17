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
from app.users.schemas import (
    ChangePasswordRequest,
    SecurityPreferencesOut,
    SecurityPreferencesUpdate,
)
from app.users.service import (
    complete_onboarding_tour,
    change_password,
    update_security_preferences,
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


@router.post("/me/password/change", status_code=200)
async def change_current_user_password(
    body: ChangePasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change an existing password.

    Separate from /me/password (which only sets a FIRST password) because the
    safety argument is different: this one is served off a session, so it
    requires the current password as proof the session is not borrowed. Every
    other session is revoked as part of the change -- see change_password.
    """
    revoked = await change_password(db, body, current_user, background_tasks)
    append_audit(
        db,
        entity_type="AUTH",
        entity_id=current_user.id,
        action="PASSWORD_CHANGED",
        actor_id=current_user.id,
        after_state={"sessions_revoked": revoked},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return {"status": "success", "sessions_revoked": revoked}


@router.get("/me/security-preferences", response_model=SecurityPreferencesOut)
async def get_security_preferences(
    current_user: User = Depends(get_current_user),
):
    return SecurityPreferencesOut(
        signin_alerts_enabled=bool(current_user.signin_alerts_enabled)
    )


@router.patch("/me/security-preferences", response_model=SecurityPreferencesOut)
async def patch_security_preferences(
    body: SecurityPreferencesUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle sign-in alerts.

    Audited: switching alerts OFF is exactly what someone who has taken over an
    account would do, so the change itself belongs in the security history.
    """
    before = bool(current_user.signin_alerts_enabled)
    user = await update_security_preferences(
        db, current_user, signin_alerts_enabled=body.signin_alerts_enabled
    )
    append_audit(
        db,
        entity_type="AUTH",
        entity_id=user.id,
        action="SIGNIN_ALERTS_CHANGED",
        actor_id=user.id,
        before_state={"signin_alerts_enabled": before},
        after_state={"signin_alerts_enabled": bool(user.signin_alerts_enabled)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return SecurityPreferencesOut(
        signin_alerts_enabled=bool(user.signin_alerts_enabled)
    )


@router.post("/me/onboarding-tour/complete")
async def complete_onboarding_tour_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark the first-run dashboard walkthrough as seen for this ACCOUNT.

    Not audited, unlike the security preferences beside it: nothing here can
    take an account away from its owner, and an audit row per dismissed tooltip
    would bury the events that matter.

    Returns the whole /me payload so the frontend can seed its cached user in
    one round trip rather than refetching after the write.
    """
    user = await complete_onboarding_tour(db, current_user)
    return user_me_payload(user)
