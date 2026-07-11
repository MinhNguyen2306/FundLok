"""HANDOFF-01 §5: register -> login -> access protected route.

Current behavior being characterized: POST /auth/login returns the user body
(UserOut), not a JSON token pair -- tokens are issued as httponly cookies
(see app/auth/router.py::_set_auth_cookies). Bearer-header auth also works
(app/utils/jwt.py::get_current_user checks the Authorization header first,
then falls back to the access_token cookie), which is what these tests use
once a token has been pulled out of the login response.

HANDOFF-02 Fix A note: only the transport changed here (httpx.AsyncClient
instead of TestClient, `async def` + `await`) -- none of the assertions
changed, because this file doesn't touch refresh-token persistence.
"""
from jose import jwt

from app.core.config import settings


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


async def test_register_then_login_issues_token_pair(client):
    email = "lifecycle-user@example.com"
    reg = await client.post(
        "/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!1", "full_name": "Lifecycle User"},
    )
    # Register returns a uniform acknowledgement (no user body) so it can't be
    # used to enumerate accounts; the created user's id comes from login below.
    assert reg.status_code == 201
    assert reg.json()["status"] == "success"

    login = await client.post("/auth/login", json={"email": email, "password": "Str0ngPassw0rd!1"})
    assert login.status_code == 200
    login_body = login.json()
    assert login_body["email"] == email
    assert login_body["role"] is None  # role is chosen later via PATCH /users/me/role
    user_id = login_body["id"]

    access_token = login.cookies.get("access_token")
    refresh_token = login.cookies.get("refresh_token")
    assert access_token and refresh_token

    access_payload = _decode(access_token)
    refresh_payload = _decode(refresh_token)
    assert access_payload["sub"] == user_id
    assert refresh_payload["sub"] == user_id
    assert refresh_payload["typ"] == "refresh"
    # Characterizes current behavior: the access token carries no "typ" claim at all.
    assert "typ" not in access_payload


async def test_register_duplicate_email_is_not_enumerable(client):
    """A second registration with an existing email returns the SAME uniform
    201 acknowledgement as a fresh one — no 400 'already registered' that would
    let an attacker enumerate accounts."""
    email = "dup-enum-user@example.com"
    first = await client.post(
        "/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!1", "full_name": "First"},
    )
    assert first.status_code == 201

    second = await client.post(
        "/auth/register",
        json={"email": email, "password": "An0therPassw0rd!2", "full_name": "Second"},
    )
    # Indistinguishable from the first response: same status and same body shape.
    assert second.status_code == 201
    assert second.json() == first.json()

    # And the duplicate did NOT overwrite the original account's password.
    login_original = await client.post(
        "/auth/login", json={"email": email, "password": "Str0ngPassw0rd!1"}
    )
    assert login_original.status_code == 200
    login_attacker = await client.post(
        "/auth/login", json={"email": email, "password": "An0therPassw0rd!2"}
    )
    assert login_attacker.status_code == 401


async def test_login_with_bad_password_returns_401(client):
    email = "bad-password-user@example.com"
    await client.post(
        "/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!1", "full_name": "Bad Password User"},
    )
    resp = await client.post("/auth/login", json={"email": email, "password": "WrongPassword!1"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Incorrect email or password"}


async def test_access_protected_route_with_valid_token_succeeds(client, make_user):
    user = await make_user()
    resp = await client.get("/users/me", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == user["id"]


async def test_access_protected_route_without_token_returns_401(client):
    resp = await client.get("/users/me")
    assert resp.status_code == 401
