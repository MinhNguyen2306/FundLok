"""Registration must never let a caller name their own role.

CLAUDE.md's role flow: users register WITHOUT a role and pick SME or INVESTOR
afterwards via PATCH /users/me/role, which restricts the choice. ADMIN and
SYSTEM_ADMIN are provisioned out-of-band.

An unused `UserCreate` schema with a `role: Role` field used to sit in
app/users/schemas.py. Nothing was bound to it — the live registration schema is
app.auth.schemas.UserCreate, which has no role field — but it was one wiring
mistake away from self-provisioned admin, so it was deleted. These tests pin the
behaviour that made it safe, so a future re-introduction fails here.
"""

import pytest
from sqlalchemy import select

from app.users.models import Role, User

PASSWORD = "test-password-123"


@pytest.mark.parametrize("attempted_role", ["ADMIN", "SYSTEM_ADMIN", "SME", "INVESTOR"])
async def test_role_in_the_registration_body_is_ignored(client, db_session, attempted_role):
    email = f"role-inject-{attempted_role.lower()}@example.com"

    resp = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": "Role Injector",
            # Not part of the schema. Pydantic's default is extra="ignore", so
            # this is dropped rather than rejected — the assertion below is what
            # proves it never reached the row.
            "role": attempted_role,
        },
    )
    assert resp.status_code == 201, resp.text

    user = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    assert user.role is None, f"registration granted role={user.role!r}"


async def test_privileged_roles_are_not_self_selectable_after_registration(client, make_user):
    """The other half: the endpoint that DOES take a role only takes two."""
    user = await make_user()  # registered, no role yet

    for role in (Role.ADMIN.value, Role.SYSTEM_ADMIN.value):
        resp = await client.patch(
            "/users/me/role", json={"role": role}, headers=user["headers"]
        )
        assert resp.status_code == 422, f"{role} was accepted: {resp.text}"


async def test_a_selectable_role_still_works(client, make_user, db_session):
    user = await make_user()

    resp = await client.patch(
        "/users/me/role", json={"role": "SME"}, headers=user["headers"]
    )

    assert resp.status_code == 200, resp.text
    row = (
        await db_session.execute(select(User).where(User.id == user["id"]))
    ).scalar_one()
    assert row.role == Role.SME.value


async def test_the_deleted_registration_schema_has_not_come_back():
    """A structural guard, not a behavioural one.

    The risk was never a live endpoint — it was a schema lying around with a
    client-settable `role` that a future endpoint could bind by accident. This
    asserts the shape stays gone.
    """
    import app.users.schemas as users_schemas

    assert not hasattr(users_schemas, "UserCreate"), (
        "app.users.schemas.UserCreate is back. Registration binds "
        "app.auth.schemas.UserCreate, which has no `role` field — do not add a "
        "registration schema here that does."
    )

    from app.auth.schemas import UserCreate as LiveUserCreate

    assert "role" not in LiveUserCreate.model_fields, (
        "the live registration schema grew a `role` field — a registrant could "
        "now name their own role, including ADMIN"
    )
