"""A social sign-in is a sign-in.

Google sign-in goes through app/oauth/, not app/auth/service.login, and it used
to call create_token_pair() with no arguments beyond the user id. The visible
consequences on /dashboard/security were:

  * every Google session showed "Unknown device · Unknown browser"
  * no SIGN_IN row appeared in recent activity
  * new-device alerts never fired, no matter what the preference said

and one invisible one: the endpoint set persistent cookies inline without the
"remember_session" marker, so /auth/refresh downgraded them to session cookies
on the first rotation.

These tests pin all four. The provider's ID-token verification is stubbed --
the point here is the session bookkeeping, not Google's JWKS.
"""
import pytest
from sqlalchemy import select

from app.oauth.schema import OAuthProvider
from app.oauth.service import GoogleOAuthProvider
from app.users.models import RefreshToken, User
from conftest import auth_headers

EDGE_WINDOWS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"
)


@pytest.fixture
def stub_google(monkeypatch):
    """Make the Google provider accept a fake ID token for a given email."""

    def _stub(email: str):
        monkeypatch.setattr(
            GoogleOAuthProvider,
            "verify_token",
            lambda self, token: {
                "sub": "google-oauth-subject",
                "email": email,
                "email_verified": True,
                "name": "OAuth User",
            },
        )

    return _stub


async def _oauth_login(client, *, user_agent: str = EDGE_WINDOWS):
    return await client.post(
        "/auth/oauth/login",
        json={"provider": OAuthProvider.GOOGLE.value, "token": "fake-id-token"},
        headers={"user-agent": user_agent},
    )


async def test_oauth_session_records_the_device(
    client, make_user, stub_google, db_session
):
    user = await make_user()
    stub_google(user["email"])

    resp = await _oauth_login(client)
    assert resp.status_code == 200, resp.text

    rows = (
        await db_session.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user["id"])
            .order_by(RefreshToken.created_at.desc())
        )
    ).scalars().all()
    newest = rows[0]
    assert newest.user_agent == EDGE_WINDOWS, "the device must be recorded"
    assert newest.ip_address is not None
    assert newest.session_id is not None


async def test_oauth_session_is_legible_on_the_security_screen(
    client, make_user, stub_google
):
    user = await make_user()
    stub_google(user["email"])
    await _oauth_login(client)

    sessions = (
        await client.get("/auth/sessions", headers=auth_headers(user))
    ).json()
    oauth_session = [s for s in sessions if s["device"] == "Windows PC"]
    assert oauth_session, sessions
    assert oauth_session[0]["browser"] == "Edge 139"
    assert oauth_session[0]["device"] != "Unknown device"


async def test_oauth_signin_appears_in_security_history(
    client, make_user, stub_google
):
    user = await make_user()
    stub_google(user["email"])
    await _oauth_login(client)

    events = (
        await client.get("/auth/security-events", headers=auth_headers(user))
    ).json()
    signins = [e for e in events if e["action"] == "SIGN_IN"]
    assert signins, events


async def test_oauth_signin_sends_the_new_device_alert(
    client, make_user, stub_google, monkeypatch
):
    sent: list[dict] = []
    monkeypatch.setattr(
        "app.oauth.service.send_new_device_signin_alert",
        lambda to_email, **kwargs: sent.append({"to": to_email, **kwargs}),
    )

    user = await make_user()
    await client.patch(
        "/users/me/security-preferences",
        json={"signin_alerts_enabled": True},
        headers=auth_headers(user),
    )
    stub_google(user["email"])

    await _oauth_login(client)
    assert len(sent) == 1, sent
    assert sent[0]["device"] == "Windows PC"
    assert sent[0]["browser"] == "Edge 139"

    # Familiar device on the second sign-in -> no repeat alert.
    await _oauth_login(client)
    assert len(sent) == 1


async def test_oauth_login_sets_the_remember_marker(client, make_user, stub_google):
    """Without it, /auth/refresh turns these persistent cookies into session
    cookies and the user is signed out on their next browser restart."""
    user = await make_user()
    stub_google(user["email"])

    resp = await _oauth_login(client)
    cookies = resp.headers.get_list("set-cookie")
    assert any(c.startswith("remember_session=") for c in cookies), cookies

    refreshed = await client.post("/auth/refresh")
    assert refreshed.status_code == 200, refreshed.text
    refresh_cookie = next(
        c for c in refreshed.headers.get_list("set-cookie")
        if c.startswith("refresh_token=")
    )
    assert "Max-Age=" in refresh_cookie
