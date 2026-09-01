from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from typing import List, Union
from uuid import UUID

from app.auth.schemas import (
    TotpChallengeOut,
    TotpDisableRequest,
    TotpEnableOut,
    TotpEnableRequest,
    TotpLoginRequest,
    TotpSetupOut,
    TotpStatusOut,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    ResendVerificationRequest,
    RegisterResponse,
    ResetPasswordRequest,
    SecurityEventOut,
    SessionOut,
    Token,
    UserCreate,
    UserOut,
)
from app.auth import service
from app.auth.user_agent import describe_browser, describe_device
from app.users.models import User
from app.utils.audit import append_audit
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_COOKIE_MAX_AGE = 30 * 60  # 30 minutes
REFRESH_COOKIE_MAX_AGE = 14 * 24 * 60 * 60  # 14 days

# "Keep me signed in" marker. The refresh endpoint re-issues both auth cookies,
# so it has to know whether the user asked for a persistent session -- without
# this, a remembered session would silently degrade to a session cookie on the
# first token refresh. httpOnly like the others: only the server reads it, and
# it carries no credential, just the choice.
REMEMBER_COOKIE = "remember_session"


def _set_auth_cookies(response: Response, tokens: dict, *, remember: bool) -> None:
    """Issue the auth cookies, persistent or session-scoped.

    remember=True  -> Max-Age set, so the browser keeps the cookies across
                      restarts and the user stays signed in for the refresh
                      token's lifetime (14 days).
    remember=False -> no Max-Age, i.e. session cookies. The browser drops them
                      when it closes, which is what a user on a shared machine
                      expects when they leave the box unticked. The tokens
                      themselves are unchanged: their own expiry still applies,
                      this only controls how long the browser holds them.
    """
    access_max_age = ACCESS_COOKIE_MAX_AGE if remember else None
    refresh_max_age = REFRESH_COOKIE_MAX_AGE if remember else None

    response.set_cookie(
        key="access_token", value=tokens["access_token"],
        httponly=True, samesite="lax", secure=False, max_age=access_max_age,
    )
    response.set_cookie(
        key="refresh_token", value=tokens["refresh_token"],
        httponly=True, samesite="lax", secure=False, max_age=refresh_max_age,
    )

    if remember:
        response.set_cookie(
            key=REMEMBER_COOKIE, value="1",
            httponly=True, samesite="lax", secure=False,
            max_age=REFRESH_COOKIE_MAX_AGE,
        )
    else:
        # Clear a marker left by an earlier remembered login on this browser,
        # otherwise the next refresh would re-persist a session the user just
        # asked not to keep.
        response.delete_cookie(key=REMEMBER_COOKIE, httponly=True, samesite="lax")


@router.post("/login", response_model=Union[TotpChallengeOut, UserOut])
async def simple_login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    user, tokens = await service.login(
        db,
        login_data,
        user_agent=user_agent,
        ip_address=ip_address,
        background_tasks=background_tasks,
    )
    # 2FA pending: no cookies, no SIGN_IN audit — nobody is signed in yet. The
    # event is recorded in the second step, so the security history never shows
    # a sign-in that was abandoned at the code prompt.
    if tokens.get("totp_required"):
        return TotpChallengeOut(challenge_token=tokens["challenge_token"])

    # Security history: the sign-in itself is the event a user scans for when
    # they suspect someone else is in the account.
    append_audit(
        db,
        entity_type="SESSION",
        entity_id=user.id,
        action="SIGN_IN",
        actor_id=user.id,
        after_state={"user_agent": user_agent},
        ip_address=ip_address,
    )
    await db.commit()
    _set_auth_cookies(response, tokens, remember=login_data.remember_me)
    return user


@router.post("/login/2fa", response_model=UserOut)
async def complete_two_factor_login(
    request: Request,
    response: Response,
    body: TotpLoginRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Second half of a 2FA sign-in: challenge token + code -> session.

    Deliberately reachable without a session — the caller has no session yet,
    that is the point. The challenge token is the credential, it expires in five
    minutes, and it cannot be used as a session itself (get_current_user rejects
    purpose-scoped tokens).
    """
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host if request.client else None
    user, tokens = await service.complete_totp_login(
        db,
        body.challenge_token,
        body.code,
        user_agent=user_agent,
        ip_address=ip_address,
        background_tasks=background_tasks,
    )
    append_audit(
        db,
        entity_type="SESSION",
        entity_id=user.id,
        action="SIGN_IN",
        actor_id=user.id,
        after_state={"user_agent": user_agent, "second_factor": "TOTP"},
        ip_address=ip_address,
    )
    await db.commit()
    _set_auth_cookies(response, tokens, remember=body.remember_me)
    return user


# --- 2FA enrolment (authenticated) ----------------------------------------- #


@router.get("/2fa", response_model=TotpStatusOut)
async def two_factor_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TotpStatusOut(
        enabled=bool(current_user.totp_enabled),
        confirmed_at=current_user.totp_confirmed_at,
        recovery_codes_remaining=await service.count_unused_recovery_codes(
            db, current_user.id
        ),
    )


@router.post("/2fa/setup", response_model=TotpSetupOut, status_code=status.HTTP_201_CREATED)
async def start_two_factor_setup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    secret, uri = await service.start_totp_setup(db, current_user)
    await db.commit()
    return TotpSetupOut(secret=secret, provisioning_uri=uri)


@router.post("/2fa/enable", response_model=TotpEnableOut)
async def enable_two_factor(
    request: Request,
    body: TotpEnableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    codes = await service.enable_totp(db, current_user, body.code)
    append_audit(
        db,
        entity_type="USER",
        entity_id=current_user.id,
        action="TOTP_ENABLED",
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return TotpEnableOut(enabled=True, recovery_codes=codes)


@router.post("/2fa/disable", response_model=TotpStatusOut)
async def disable_two_factor(
    request: Request,
    body: TotpDisableRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await service.disable_totp(db, current_user, body.password, body.code)
    append_audit(
        db,
        entity_type="USER",
        entity_id=current_user.id,
        action="TOTP_DISABLED",
        actor_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return TotpStatusOut(
        enabled=False, confirmed_at=None, recovery_codes_remaining=0
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.register_user(db, user, background_tasks)


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    return await service.verify_email(db, token)


@router.post("/resend-verification")
async def resend_verification(body: ResendVerificationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.resend_verification(db, body.email, background_tasks)


@router.post("/refresh", response_model=Token)
async def refresh_tokens(request: Request, response: Response, body: RefreshRequest = None, db: AsyncSession = Depends(get_db)):
    refresh_token = body.refresh_token if body and body.refresh_token else request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    tokens = await service.refresh_token_pair(
        db,
        refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    # Preserve the login-time choice: the marker cookie is the only thing that
    # survives to tell us, since the request carries no body flag here.
    remember = request.cookies.get(REMEMBER_COOKIE) == "1"
    _set_auth_cookies(response, tokens, remember=remember)
    return tokens


@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    # HANDOFF-02 Fix B: revoke the presented refresh token server-side, not
    # just clear the cookie -- a stolen token no longer stays valid until
    # natural expiry after the legitimate user logs out.
    refresh_token = request.cookies.get("refresh_token")
    result = await service.logout(db, refresh_token)
    await db.commit()
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    response.delete_cookie(key="refresh_token", httponly=True, samesite="lax")
    response.delete_cookie(key=REMEMBER_COOKIE, httponly=True, samesite="lax")
    return result


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    return await service.forgot_password(db, body, background_tasks)


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    return await service.reset_password(db, body, background_tasks)


@router.get("/sessions", response_model=List[SessionOut])
async def list_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Devices currently signed in to this account.

    Backed by `refresh_tokens`: an unrevoked, unexpired row is a live sign-in.
    The caller's own session is flagged rather than hidden, so the UI can label
    it "this device" and disable its revoke button.
    """
    sessions = await service.list_sessions(
        db, current_user.id, current_token=request.cookies.get("refresh_token")
    )
    return [
        SessionOut(
            session_id=item["session_id"],
            device=describe_device(item["user_agent"]),
            browser=describe_browser(item["user_agent"]),
            ip_address=item["ip_address"],
            created_at=item["created_at"],
            last_used_at=item["last_used_at"],
            current=item["current"],
        )
        for item in sessions
    ]


@router.post("/sessions/{session_id}/revoke")
async def revoke_session(
    session_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sign one device out. Scoped to the caller's own sessions."""
    result = await service.revoke_session(
        db,
        current_user.id,
        session_id,
        current_token=request.cookies.get("refresh_token"),
    )
    append_audit(
        db,
        entity_type="SESSION",
        entity_id=current_user.id,
        action="SESSION_REVOKED",
        actor_id=current_user.id,
        after_state={"session_id": str(session_id)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return result


@router.post("/sessions/revoke-others")
async def revoke_other_sessions(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sign out everywhere except the device making this call."""
    result = await service.revoke_other_sessions(
        db, current_user.id, current_token=request.cookies.get("refresh_token")
    )
    append_audit(
        db,
        entity_type="SESSION",
        entity_id=current_user.id,
        action="SESSIONS_REVOKED_OTHERS",
        actor_id=current_user.id,
        after_state=result,
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return result


# How loudly the security screen should present each action. Anything not listed
# is routine — a new audited action shows up as information rather than
# silently becoming an alarm.
_EVENT_SEVERITY = {
    "SIGN_IN_FAILED": "critical",
    "SESSION_REVOKED": "warning",
    "SESSIONS_REVOKED_OTHERS": "warning",
    "PASSWORD_RESET": "warning",
}


@router.get("/security-events", response_model=List[SecurityEventOut])
async def list_security_events(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """This account's recent security history, newest first.

    Read from `audit_logs` filtered to the caller as actor. It is deliberately
    not every audit row for the user's entities — a project edit is not
    security history — so only SESSION and AUTH entity types are returned.
    """
    rows = await service.list_security_events(
        db, current_user.id, limit=min(max(limit, 1), 100)
    )
    return [
        SecurityEventOut(
            id=row.id,
            action=row.action,
            entity_type=row.entity_type,
            severity=_EVENT_SEVERITY.get(row.action, "info"),
            ip_address=row.ip_address,
            created_at=row.created_at,
        )
        for row in rows
    ]
