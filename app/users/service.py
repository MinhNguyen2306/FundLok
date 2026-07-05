from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.users.models import Role, User
from app.users.schemas import (
    AVATAR_CONTENT_TYPE_EXTENSIONS,
    AVATAR_MAX_SIZE,
    AvatarConfirmRequest,
    AvatarPresignRequest,
    UserUpdateRequest,
)
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
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


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
