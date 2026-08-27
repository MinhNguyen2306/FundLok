from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from datetime import datetime, timezone

from app.users.models import RefreshToken, Role, User
from app.users.schemas import (
    ChangePasswordRequest,
    AVATAR_CONTENT_TYPE_EXTENSIONS,
    AVATAR_MAX_SIZE,
    AvatarConfirmRequest,
    AvatarPresignRequest,
    SetPasswordRequest,
    UserUpdateRequest,
)
from app.utils.email import send_password_changed_notice
from app.utils.password import hash_password, verify_password
from app.utils.r2 import delete_object, head_object, presign_get, presign_put


def build_avatar_url(user: User) -> str | None:
    """Fresh presigned GET URL for the user's avatar, or None.

    Falls back to None (rather than failing the profile request) when no avatar
    is set or object storage is not configured for this environment.
    """
    if not user.avatar_key:
        return None
    try:
        return presign_get(user.avatar_key)
    except HTTPException:
        return None


def user_me_payload(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "status": user.status,
        "email_verified": user.email_verified,
        "bio": user.bio,
        "avatar_url": build_avatar_url(user),
        # Lets the profile page tell "change your password" from "set one for
        # the first time" (OAuth-only accounts have no hash). Never expose the
        # hash itself.
        "has_password": bool(user.password_hash),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


async def set_password(
    db: AsyncSession,
    body: SetPasswordRequest,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> None:
    """Give a passwordless account its first password.

    Only ever a *first* password. An account that already has one is refused
    and pointed at forgot-password, where the emailed token proves control of
    the mailbox. That split is what makes this endpoint safe to serve off a
    session alone: setting a first password can't take an account away from
    anyone (there was no password login to lose), whereas overwriting an
    existing one off a borrowed session would be account takeover.

    NOTE: no account can currently reach this branch -- `users.password_hash`
    is NOT NULL and registration always sets it, so every existing user is
    rejected below. It becomes reachable once OAuth sign-in creates accounts
    without a password; see the endpoint docstring.
    """
    if current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account already has a password. Use Forgot password to change it.",
        )

    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)
    await db.commit()

    # Queued only after the commit, so the notice can't describe a change that
    # didn't land. `first_time=True` because "your password was changed" would
    # be untrue for an account that never had one.
    background_tasks.add_task(
        send_password_changed_notice, to_email=current_user.email, first_time=True
    )


async def update_user_profile(db: AsyncSession, body: UserUpdateRequest, current_user: User) -> User:
    # PATCH semantics: only touch fields the client actually sent. Sending an
    # explicit null clears the field; omitting it leaves the value unchanged.
    data = body.model_dump(exclude_unset=True)

    if "phone" in data:
        phone = data["phone"]
        if phone is not None:
            result = await db.execute(
                select(User).where(User.phone == phone, User.id != current_user.id)
            )
            clash = result.scalar_one_or_none()
            if clash:
                raise HTTPException(status_code=400, detail="Phone number already registered")
        current_user.phone = phone

    if "full_name" in data:
        current_user.full_name = data["full_name"]

    if "bio" in data:
        current_user.bio = data["bio"]

    db.add(current_user)
    await db.flush()
    return current_user


async def select_user_role(db: AsyncSession, role: Role, current_user: User) -> User:
    # One-time selection: once a role is set it can't be changed here, which
    # prevents a user from later switching into a different role on their own.
    if current_user.role:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Role has already been set",
        )
    current_user.role = role.value
    db.add(current_user)
    await db.flush()
    return current_user


def _avatar_key(user_id, ext: str) -> str:
    # One avatar per user; the deterministic key means a new upload of the same
    # type overwrites the previous object.
    return f"user/{user_id}/avatar.{ext}"


def create_avatar_presign(body: AvatarPresignRequest, current_user: User) -> tuple[str, str, int]:
    ext = AVATAR_CONTENT_TYPE_EXTENSIONS.get(body.content_type)
    if ext is None:
        allowed = ", ".join(sorted(AVATAR_CONTENT_TYPE_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported avatar content_type (allowed: {allowed})",
        )
    if body.size > AVATAR_MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Avatar too large (max {AVATAR_MAX_SIZE} bytes)",
        )
    file_key = _avatar_key(current_user.id, ext)
    upload_url = presign_put(file_key, body.content_type)
    return file_key, upload_url, settings.R2_PRESIGN_EXPIRE_SECONDS


async def confirm_avatar(db: AsyncSession, body: AvatarConfirmRequest, current_user: User) -> User:
    # The client never picks an arbitrary key: it must be the one we issued for
    # this user, so a caller cannot point their avatar at someone else's object.
    expected_prefix = f"user/{current_user.id}/avatar."
    if not body.file_key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="file_key does not belong to this user")

    head = head_object(body.file_key)
    if head is None:
        raise HTTPException(status_code=400, detail="Object not found in storage")
    if head["size"] and head["size"] > AVATAR_MAX_SIZE:
        raise HTTPException(status_code=400, detail="Uploaded avatar too large")

    old_key = current_user.avatar_key
    if old_key and old_key != body.file_key:
        # Extension changed (e.g. png -> jpg): the old object would be orphaned.
        delete_object(old_key)

    current_user.avatar_key = body.file_key
    db.add(current_user)
    await db.flush()
    return current_user


async def change_password(
    db: AsyncSession,
    body: ChangePasswordRequest,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> int:
    """Change an existing password, proving control with the current one.

    Two things beyond swapping the hash, both of which are the point of the
    feature rather than extras:

      * every OTHER session is revoked. Changing a password because you think
        someone else is in the account achieves nothing if their session keeps
        working -- refresh tokens are independent of the password.
      * the owner is emailed. Same reasoning as set_password: an unauthorised
        change has to be visible to the real owner while they can still act.

    Returns the number of sessions revoked so the caller can tell the user.
    """
    if not current_user.password_hash:
        # No password to change; that path is set_password, which is safe
        # precisely because there is nothing to overwrite.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account has no password yet. Set one instead.",
        )

    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if verify_password(body.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current one",
        )

    current_user.password_hash = hash_password(body.new_password)
    db.add(current_user)

    revoked = 0
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    now = datetime.now(timezone.utc)
    for row in result.scalars().all():
        row.revoked_at = now
        db.add(row)
        revoked += 1

    await db.commit()

    # Queued after the commit so the notice can never describe a change that
    # was rolled back.
    background_tasks.add_task(send_password_changed_notice, current_user.email)
    return revoked


async def update_security_preferences(
    db: AsyncSession, current_user: User, *, signin_alerts_enabled: bool
) -> User:
    current_user.signin_alerts_enabled = signin_alerts_enabled
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return current_user
