from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.users.models import Role, User
from app.utils.jwt import get_current_user


def require_roles(*allowed: Role) -> Callable[..., User]:
    allowed_values = {r.value for r in allowed}

    def _dep(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized for this action",
            )
        return current_user

    return _dep
