from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.oauth.schema import OAuthLoginRequest, OAuthTokenResponse
from app.auth.router import _set_auth_cookies
from app.oauth.service import OAuthService
from app.utils.audit import append_audit


router = APIRouter(prefix="/auth/oauth", tags=["oauth"])


@router.post("/login", response_model=OAuthTokenResponse)
async def oauth_login(
    body: OAuthLoginRequest,
    request: Request,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None

    user, tokens, _is_new_device = await OAuthService(db).login(
        body.provider,
        body.token,
        user_agent=user_agent,
        ip_address=ip_address,
        background_tasks=background_tasks,
    )

    # Same audit row as the password path, or a social sign-in would be
    # invisible in the account's security history.
    append_audit(
        db,
        entity_type="SESSION",
        entity_id=user.id,
        action="SIGN_IN",
        actor_id=user.id,
        after_state={"provider": body.provider.value, "user_agent": user_agent},
        ip_address=ip_address,
    )
    await db.commit()

    # The shared helper rather than inline set_cookie calls: it also writes the
    # "remember_session" marker, without which /auth/refresh would downgrade
    # these persistent cookies to session cookies on the first rotation and log
    # the user out on their next browser restart.
    #
    # remember=True because a social sign-in carries no "keep me signed in"
    # checkbox — the redirect leaves nowhere to put one — and silently choosing
    # the shorter session would be a worse surprise than the longer one.
    _set_auth_cookies(response, tokens, remember=True)

    return tokens
