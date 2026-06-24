"""Tests for post-registration role selection (PUT /users/me/role).

The core invariant under test: a user may only self-assign SME or INVESTOR.
Anything else — a privileged role (ADMIN / SYSTEM_ADMIN) or a value that is not
a role at all — must be rejected, and a role can only be chosen once.
"""
import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

import app.main as main_module
from app.core.database import get_db
from app.main import app
from app.users.models import Role, User
from app.users.schemas import SELECTABLE_ROLES, RoleSelectRequest
from app.users.service import select_user_role
from app.utils.jwt import get_current_user


# --------------------------------------------------------------------------- #
# Schema-level: this is where the SME/INVESTOR-only constraint actually lives.
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("value", ["SME", "INVESTOR"])
def test_selectable_roles_accepted(value):
    assert RoleSelectRequest(role=value).role is Role(value)


@pytest.mark.parametrize("value", ["ADMIN", "SYSTEM_ADMIN"])
def test_privileged_roles_rejected(value):
    # Valid Role enum members, but never self-selectable.
    with pytest.raises(ValidationError):
        RoleSelectRequest(role=value)


@pytest.mark.parametrize("value", ["", "sme", "investor", "FOO", "guest", 123, None])
def test_non_role_values_rejected(value):
    # Not members of the Role enum at all (note: matching is case-sensitive).
    with pytest.raises(ValidationError):
        RoleSelectRequest(role=value)


def test_missing_role_rejected():
    with pytest.raises(ValidationError):
        RoleSelectRequest()


def test_selectable_roles_constant_excludes_privileged():
    assert set(SELECTABLE_ROLES) == {Role.SME, Role.INVESTOR}


# --------------------------------------------------------------------------- #
# Service-level: one-time selection (can't overwrite an existing role).
# --------------------------------------------------------------------------- #

class _FakeDB:
    """Minimal stand-in for a SQLAlchemy session for these handlers."""

    def __init__(self):
        self.added = []
        self.flushed = False
        self.committed = False

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        self.flushed = True

    def commit(self):
        self.committed = True


def _user(role=None):
    return User(id=uuid.uuid4(), email="u@example.com", role=role, status="ACTIVE")


def test_select_role_sets_role_when_unset():
    db, user = _FakeDB(), _user(role=None)
    out = select_user_role(db, Role.INVESTOR, user)
    assert out.role == "INVESTOR"
    assert db.flushed is True


def test_select_role_conflicts_when_already_set():
    db, user = _FakeDB(), _user(role="SME")
    with pytest.raises(HTTPException) as exc:
        select_user_role(db, Role.INVESTOR, user)
    assert exc.value.status_code == 409
    assert user.role == "SME"  # unchanged


# --------------------------------------------------------------------------- #
# Endpoint-level: PUT /users/me/role end to end (no DB / auth required).
# --------------------------------------------------------------------------- #

@pytest.fixture(autouse=True)
def _disable_maintenance():
    # The maintenance middleware would otherwise hit the DB on /users requests.
    with patch.object(main_module, "is_maintenance_active", return_value=(False, None)):
        yield


@pytest.fixture
def make_client():
    created = []

    def _make(user):
        db = _FakeDB()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        created.append(db)
        # No `with` block: avoids running lifespan/startup (and real DB connects).
        return TestClient(app), db

    yield _make
    app.dependency_overrides.clear()


@pytest.mark.parametrize("role", ["SME", "INVESTOR"])
def test_put_role_accepts_selectable(make_client, role):
    client, db = make_client(_user(role=None))
    resp = client.put("/users/me/role", json={"role": role})
    assert resp.status_code == 200
    assert resp.json()["role"] == role
    assert db.committed is True


@pytest.mark.parametrize("role", ["ADMIN", "SYSTEM_ADMIN", "FOO", "sme", ""])
def test_put_role_rejects_everything_else(make_client, role):
    client, db = make_client(_user(role=None))
    resp = client.put("/users/me/role", json={"role": role})
    assert resp.status_code == 422
    assert db.committed is False


def test_put_role_conflict_when_already_set(make_client):
    client, _ = make_client(_user(role="SME"))
    resp = client.put("/users/me/role", json={"role": "INVESTOR"})
    assert resp.status_code == 409


def test_put_role_requires_authentication():
    # Only override get_db so the real auth dependency runs and rejects.
    app.dependency_overrides[get_db] = lambda: _FakeDB()
    try:
        client = TestClient(app)
        resp = client.put("/users/me/role", json={"role": "SME"})
        assert resp.status_code in (401, 403)
    finally:
        app.dependency_overrides.clear()
