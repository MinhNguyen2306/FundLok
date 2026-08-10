"""POST /users/me/password — set a FIRST password from the profile page.

The split this protects: setting a first password is safe off a session alone
(there was no password login to take away), but *changing* an existing one is
not, so it belongs to forgot-password / reset-password where the emailed token
proves the mailbox. This endpoint therefore refuses any account that already
has a password.

Note every account currently has one -- `users.password_hash` is NOT NULL and
registration always sets it -- so the passwordless branch is exercised here by
clearing the hash directly. That branch goes live when OAuth sign-in starts
creating accounts without a password.
"""
from sqlalchemy import select

from app.users.models import User

NEW_PASSWORD = "A-Brand-New-Passw0rd!"


async def test_set_password_is_refused_when_one_already_exists(client, make_user):
    """The whole point of the endpoint: a session must never be able to
    overwrite an existing password. Those users go through forgot-password."""
    user = await make_user()

    resp = await client.post(
        "/users/me/password",
        json={"new_password": NEW_PASSWORD},
        headers=user["headers"],
    )
    assert resp.status_code == 400
    assert resp.json() == {
        "detail": "This account already has a password. Use Forgot password to change it."
    }

    # Untouched — the original password still logs in.
    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert login.status_code == 200


async def test_set_password_succeeds_for_a_passwordless_account(client, make_user, db_session):
    """The OAuth case, simulated by clearing the hash a registration left behind."""
    user = await make_user()

    db_user = (
        await db_session.execute(select(User).where(User.email == user["email"]))
    ).scalar_one()
    db_user.password_hash = None
    await db_session.commit()

    resp = await client.post(
        "/users/me/password",
        json={"new_password": NEW_PASSWORD},
        headers=user["headers"],
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "success"

    login = await client.post(
        "/auth/login", json={"email": user["email"], "password": NEW_PASSWORD}
    )
    assert login.status_code == 200


async def test_setting_a_password_emails_the_owner(client, make_user, db_session, monkeypatch):
    """A credential change the owner didn't make has to be visible to them, so
    every successful set/change sends a notice."""
    sent: list[dict] = []
    monkeypatch.setattr(
        "app.users.service.send_password_changed_notice",
        lambda to_email, first_time=False: sent.append(
            {"to": to_email, "first_time": first_time}
        ),
    )

    user = await make_user()
    db_user = (
        await db_session.execute(select(User).where(User.email == user["email"]))
    ).scalar_one()
    db_user.password_hash = None
    await db_session.commit()

    resp = await client.post(
        "/users/me/password",
        json={"new_password": NEW_PASSWORD},
        headers=user["headers"],
    )
    assert resp.status_code == 200
    # first_time=True: "your password was changed" would be untrue here.
    assert sent == [{"to": user["email"], "first_time": True}]


async def test_a_refused_set_password_sends_no_email(client, make_user, monkeypatch):
    """No notice when nothing changed — a false 'your password changed' alert
    is exactly the noise that trains people to ignore the real one."""
    sent: list[str] = []
    monkeypatch.setattr(
        "app.users.service.send_password_changed_notice",
        lambda to_email, first_time=False: sent.append(to_email),
    )

    user = await make_user()  # already has a password -> refused
    resp = await client.post(
        "/users/me/password",
        json={"new_password": NEW_PASSWORD},
        headers=user["headers"],
    )
    assert resp.status_code == 400
    assert sent == []


async def test_passwordless_account_cannot_log_in_with_a_password(client, make_user, db_session):
    """password_hash became nullable, so authenticate_user has to reject a
    passwordless account itself -- handing None to passlib raises, which would
    turn an ordinary failed login into a 500."""
    user = await make_user()

    db_user = (
        await db_session.execute(select(User).where(User.email == user["email"]))
    ).scalar_one()
    db_user.password_hash = None
    await db_session.commit()

    resp = await client.post(
        "/auth/login", json={"email": user["email"], "password": user["password"]}
    )
    assert resp.status_code == 401


async def test_set_password_rejects_a_short_password(client, make_user):
    user = await make_user()

    resp = await client.post(
        "/users/me/password",
        json={"new_password": "short1"},
        headers=user["headers"],
    )
    assert resp.status_code == 422


async def test_set_password_requires_authentication(client):
    resp = await client.post("/users/me/password", json={"new_password": NEW_PASSWORD})
    assert resp.status_code == 401


async def test_users_me_reports_whether_a_password_is_set(client, make_user):
    """Drives the profile page's choice between "Set password" (opens the
    dialog) and "Change password" (sends the user to forgot-password)."""
    user = await make_user()
    resp = await client.get("/users/me", headers=user["headers"])
    assert resp.status_code == 200
    assert resp.json()["has_password"] is True
