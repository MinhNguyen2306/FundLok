"""HANDOFF-01 §5: register -> login -> access protected route.

Current behavior being characterized: POST /auth/login returns the user body
(UserOut), not a JSON token pair -- tokens are issued as httponly cookies
(see app/auth/router.py::_set_auth_cookies). Bearer-header auth also works
(app/utils/jwt.py::get_current_user checks the Authorization header first,
then falls back to the access_token cookie), which is what these tests use
once a token has been pulled out of the login response.
"""
from jose import jwt

from app.core.config import settings


def _decode(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def test_register_then_login_issues_token_pair(client):
    email = "lifecycle-user@example.com"
    reg = client.post(
        "/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!1", "full_name": "Lifecycle User"},
    )
    assert reg.status_code == 200
    body = reg.json()
    assert body["email"] == email
    assert body["role"] is None  # role is chosen later via PATCH /users/me/role
    user_id = body["id"]

    login = client.post("/auth/login", json={"email": email, "password": "Str0ngPassw0rd!1"})
    assert login.status_code == 200

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


def test_login_with_bad_password_returns_401(client):
    email = "bad-password-user@example.com"
    client.post(
        "/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!1", "full_name": "Bad Password User"},
    )
    resp = client.post("/auth/login", json={"email": email, "password": "WrongPassword!1"})
    assert resp.status_code == 401
    assert resp.json() == {"detail": "Incorrect email or password"}


def test_access_protected_route_with_valid_token_succeeds(client, make_user):
    user = make_user()
    resp = client.get("/users/me", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["id"] == user["id"]


def test_access_protected_route_without_token_returns_401(client):
    resp = client.get("/users/me")
    assert resp.status_code == 401
