"""HANDOFF-01 §5: refresh & logout.

Current behavior being characterized (documented deliberately, per HANDOFF-01
§3.2): refresh tokens are stateless JWTs. create_token_pair() in
app/auth/service.py never touches the refresh_tokens table -- there is no
server-side revocation. HANDOFF-02 changes this on purpose; these tests are
the regression guard that will need updating when it does.
"""
from datetime import timedelta

from jose import jwt

from app.core.config import settings
from app.utils.jwt import create_access_token


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def test_refresh_with_valid_refresh_token_returns_new_pair(client, make_user):
    user = make_user()
    resp = client.post("/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]

    access_payload = _decode(body["access_token"])
    refresh_payload = _decode(body["refresh_token"])
    assert access_payload["sub"] == user["id"]
    assert refresh_payload["sub"] == user["id"]
    assert refresh_payload["typ"] == "refresh"
    assert "typ" not in access_payload

    # Cookies are refreshed too.
    assert resp.cookies.get("access_token") == body["access_token"]
    assert resp.cookies.get("refresh_token") == body["refresh_token"]


def test_refresh_with_access_token_typ_rejected(client, make_user):
    user = make_user()
    # The access token has no "typ" claim, so it fails the refresh endpoint's
    # `payload.get("typ") != "refresh"` check.
    resp = client.post("/auth/refresh", json={"refresh_token": user["access_token"]})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or expired refresh token"}


def test_refresh_with_tampered_token_returns_401(client, make_user):
    user = make_user()
    valid = user["refresh_token"]
    tampered = valid[:-1] + ("a" if valid[-1] != "a" else "b")
    resp = client.post("/auth/refresh", json={"refresh_token": tampered})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or expired refresh token"}


def test_refresh_with_expired_token_returns_401(client, make_user):
    user = make_user()
    expired = create_access_token(
        data={"sub": user["id"], "typ": "refresh"},
        expires_delta=timedelta(seconds=-1),
    )
    resp = client.post("/auth/refresh", json={"refresh_token": expired})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or expired refresh token"}


def test_refresh_missing_token_returns_401(client):
    resp = client.post("/auth/refresh", json={})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Refresh token missing"}


def test_logout_clears_refresh_cookie(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "message": "Logged out successfully"}

    set_cookie_headers = resp.headers.get_list("set-cookie")
    access_cleared = [h for h in set_cookie_headers if h.startswith("access_token=")]
    refresh_cleared = [h for h in set_cookie_headers if h.startswith("refresh_token=")]
    assert access_cleared and refresh_cleared
    # Starlette's Response.delete_cookie expires the cookie immediately.
    assert any("Max-Age=0" in h for h in access_cleared)
    assert any("Max-Age=0" in h for h in refresh_cleared)
