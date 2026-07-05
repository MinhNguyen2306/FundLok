"""HANDOFF-01 §5 / HANDOFF-02 Fix B: refresh & logout.

INTENTIONAL BEHAVIOR CHANGE (flagged per HANDOFF-02 §Fix B, not silently
rewritten): HANDOFF-01 characterized refresh tokens as stateless JWTs --
create_token_pair() never touched the refresh_tokens table and there was no
server-side revocation. HANDOFF-02 Fix B makes refresh tokens stateful:

  - Every issued refresh token is persisted (hashed with SHA-256, see
    app/auth/service.py::hash_refresh_token) in `refresh_tokens`.
  - POST /auth/refresh now rotates: the presented token is looked up by hash
    and revoked, and the *old* token can never be reused again (reuse
    detection), which was not true before.
  - POST /auth/logout now revokes the presented refresh token server-side,
    not just clears the cookie.

Tests below that only exercise input validation (missing/tampered/expired/
wrong-typ tokens) are unaffected, since those all fail before any DB lookup
and keep their original assertions. Three tests are new, added specifically
for Fix B: test_reused_refresh_token_after_rotation_is_rejected,
test_logout_revokes_refresh_token_server_side, and
test_refresh_token_hash_not_stored_in_plaintext.
"""
from datetime import timedelta

from jose import jwt

from app.auth.service import hash_refresh_token
from app.core.config import settings
from app.utils.jwt import create_access_token


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def test_refresh_with_valid_refresh_token_returns_new_pair(client, make_user):
    user = await make_user()
    resp = await client.post("/auth/refresh", json={"refresh_token": user["refresh_token"]})
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


async def test_refresh_with_access_token_typ_rejected(client, make_user):
    user = await make_user()
    # The access token has no "typ" claim, so it fails the refresh endpoint's
    # `payload.get("typ") != "refresh"` check -- rejected before any DB hit.
    resp = await client.post("/auth/refresh", json={"refresh_token": user["access_token"]})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or expired refresh token"}


async def test_refresh_with_tampered_token_returns_401(client, make_user):
    user = await make_user()
    valid = user["refresh_token"]
    tampered = valid[:-1] + ("a" if valid[-1] != "a" else "b")
    resp = await client.post("/auth/refresh", json={"refresh_token": tampered})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or expired refresh token"}


async def test_refresh_with_expired_token_returns_401(client, make_user):
    user = await make_user()
    expired = create_access_token(
        data={"sub": user["id"], "typ": "refresh"},
        expires_delta=timedelta(seconds=-1),
    )
    resp = await client.post("/auth/refresh", json={"refresh_token": expired})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Invalid or expired refresh token"}


async def test_refresh_missing_token_returns_401(client):
    resp = await client.post("/auth/refresh", json={})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Refresh token missing"}


async def test_logout_clears_refresh_cookie(client):
    resp = await client.post("/auth/logout")
    assert resp.status_code == 200
    assert resp.json() == {"status": "success", "message": "Logged out successfully"}

    set_cookie_headers = resp.headers.get_list("set-cookie")
    access_cleared = [h for h in set_cookie_headers if h.startswith("access_token=")]
    refresh_cleared = [h for h in set_cookie_headers if h.startswith("refresh_token=")]
    assert access_cleared and refresh_cleared
    # Starlette's Response.delete_cookie expires the cookie immediately.
    assert any("Max-Age=0" in h for h in access_cleared)
    assert any("Max-Age=0" in h for h in refresh_cleared)


# --------------------------------------------------------------------------- #
# New for HANDOFF-02 Fix B.
# --------------------------------------------------------------------------- #

async def test_refresh_token_hash_not_stored_in_plaintext(make_user, get_refresh_token_row):
    user = await make_user()
    rows = await get_refresh_token_row(user["id"])
    assert len(rows) == 1
    assert rows[0].token_hash != user["refresh_token"]
    assert rows[0].token_hash == hash_refresh_token(user["refresh_token"])


async def test_reused_refresh_token_after_rotation_is_rejected(client, make_user):
    user = await make_user()
    first = await client.post("/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert first.status_code == 200

    # The token just used for rotation is now revoked; presenting it again
    # (e.g. an attacker replaying a captured token) must be rejected.
    second = await client.post("/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert second.status_code == 401
    assert second.json() == {"detail": "Invalid or expired refresh token"}


async def test_logout_revokes_refresh_token_server_side(client, make_user, get_refresh_token_row):
    user = await make_user()

    logout_resp = await client.post(
        "/auth/logout", headers={"Cookie": f"refresh_token={user['refresh_token']}"}
    )
    assert logout_resp.status_code == 200

    rows = await get_refresh_token_row(user["id"])
    assert rows[0].revoked_at is not None

    # A revoked-by-logout token can no longer be used to refresh -- this is
    # the whole point of Fix B: logout is no longer purely a client-side
    # cookie clear.
    refresh_resp = await client.post("/auth/refresh", json={"refresh_token": user["refresh_token"]})
    assert refresh_resp.status_code == 401
    assert refresh_resp.json() == {"detail": "Invalid or expired refresh token"}
