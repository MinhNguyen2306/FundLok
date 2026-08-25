"""'Keep me signed in' — cookie persistence, not token lifetime.

The tokens are unchanged either way; what the checkbox controls is whether the
browser holds the cookies after it closes. Unticked means session cookies (no
Max-Age), which is what a user on a shared machine expects.

The subtlety worth pinning: /auth/refresh re-issues both cookies, so without a
marker a remembered session would silently degrade to a session cookie on the
first refresh — and the user would be logged out on the next browser restart
despite ticking the box.
"""
from conftest import auth_headers


def _cookie_directives(response, name: str) -> str | None:
    """The raw Set-Cookie line for `name`, or None if it was not set."""
    for header in response.headers.get_list("set-cookie"):
        if header.startswith(f"{name}="):
            return header
    return None


async def test_remember_me_true_sets_persistent_cookies(client, make_user):
    user = await make_user()
    resp = await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": True},
    )
    assert resp.status_code == 200, resp.text

    for name in ("access_token", "refresh_token"):
        directives = _cookie_directives(resp, name)
        assert directives is not None, f"{name} not set"
        assert "Max-Age=" in directives, f"{name} should persist: {directives}"

    marker = _cookie_directives(resp, "remember_session")
    assert marker is not None and "Max-Age=" in marker


async def test_remember_me_false_sets_session_cookies(client, make_user):
    user = await make_user()
    resp = await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": False},
    )
    assert resp.status_code == 200, resp.text

    for name in ("access_token", "refresh_token"):
        directives = _cookie_directives(resp, name)
        assert directives is not None, f"{name} not set"
        assert "Max-Age=" not in directives, (
            f"{name} must be a session cookie when remember_me is false: {directives}"
        )


async def test_remember_me_defaults_to_false(client, make_user):
    """An older client that does not send the field gets the safer behaviour."""
    user = await make_user()
    resp = await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"]},
    )
    assert resp.status_code == 200, resp.text
    assert "Max-Age=" not in (_cookie_directives(resp, "refresh_token") or "")


async def test_refresh_preserves_a_remembered_session(client, make_user):
    """The regression this feature would otherwise ship with."""
    user = await make_user()
    login = await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": True},
    )
    assert login.status_code == 200

    # The client carries the cookies, including the marker.
    refreshed = await client.post("/auth/refresh")
    assert refreshed.status_code == 200, refreshed.text
    assert "Max-Age=" in (_cookie_directives(refreshed, "refresh_token") or ""), (
        "a remembered session must stay persistent across a token refresh"
    )


async def test_refresh_keeps_an_unremembered_session_session_scoped(client, make_user):
    user = await make_user()
    login = await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": False},
    )
    assert login.status_code == 200

    refreshed = await client.post("/auth/refresh")
    assert refreshed.status_code == 200, refreshed.text
    assert "Max-Age=" not in (_cookie_directives(refreshed, "refresh_token") or "")


async def test_logout_clears_the_remember_marker(client, make_user):
    """Otherwise the next login on this browser inherits a choice the user did
    not make this time."""
    user = await make_user()
    await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": True},
    )
    resp = await client.post("/auth/logout")
    assert resp.status_code == 200, resp.text

    marker = _cookie_directives(resp, "remember_session")
    assert marker is not None, "logout should send a clearing Set-Cookie"
    assert 'remember_session=""' in marker or "remember_session=;" in marker


async def test_unticking_after_a_remembered_login_clears_the_marker(
    client, make_user
):
    user = await make_user()
    await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": True},
    )
    resp = await client.post(
        "/auth/login",
        json={"email": user["email"], "password": user["password"], "remember_me": False},
    )
    assert resp.status_code == 200, resp.text
    marker = _cookie_directives(resp, "remember_session")
    assert marker is not None and (
        'remember_session=""' in marker or "remember_session=;" in marker
    )
