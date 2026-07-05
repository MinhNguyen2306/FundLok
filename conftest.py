"""Shared pytest fixtures for the FundLok behavioral test suite (HANDOFF-01).

Design constraints (see docs/handoffs/HANDOFF-01-test-suite.md):
- Schema comes from real Alembic migrations (`alembic upgrade head`) against a
  throwaway Postgres, never from `Base.metadata.create_all` — that would hide
  migration drift that `alembic check` exists to catch.
- The `get_db` dependency override lives here, and only here, so the later
  async migration (HANDOFF-02) only has to touch this one seam.
- Tests are isolated by truncating all tables between tests (not per-test
  transactions), because some app code opens its own session outside of
  `get_db` (e.g. app.system.service.is_maintenance_active uses SessionLocal()
  directly), which would not see an uncommitted outer transaction.
- All external I/O (email, R2, Brankas, Didit, Turnstile) is mocked/disabled.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --------------------------------------------------------------------------- #
# Environment must be set BEFORE anything imports app.core.config, since the
# `settings` object (and the SQLAlchemy `engine` bound to it) is constructed
# once at import time.
# --------------------------------------------------------------------------- #
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://test_user:test_password@localhost:5432/test_db",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "14")
# Explicitly blank (not just "unset") so a developer's local .env can't leak a
# real Turnstile secret into the test run and make verify_turnstile_token try
# a real network call.
os.environ["CLOUDFLARE_TURNSTILE_SECRET_KEY"] = ""
# Belt-and-suspenders: never let tests touch real R2 / Didit even if a local
# .env has them configured.
os.environ["R2_ENDPOINT_URL"] = ""
os.environ["DIDIT_API_KEY"] = ""

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.database import Base, engine, get_db  # noqa: E402
from app.lending.models import Document  # noqa: E402
from app.main import app  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


def iter_endpoint_routes(routes):
    """Recursively flatten app.routes into leaf endpoint routes (path +
    methods), independent of how a given Starlette/FastAPI version represents
    included sub-routers (older versions flatten them into APIRoute objects
    directly; newer ones wrap them, e.g. fastapi.routing._IncludedRouter with
    an `original_router` attribute). Used by route-introspection tests that
    assert "no mutation route exists" for a resource."""
    for route in routes:
        original_router = getattr(route, "original_router", None)
        if original_router is not None:
            yield from iter_endpoint_routes(original_router.routes)
            continue
        sub_routes = getattr(route, "routes", None)
        if sub_routes:
            yield from iter_endpoint_routes(sub_routes)
        elif hasattr(route, "path") and hasattr(route, "methods"):
            yield route


@pytest.fixture(scope="session", autouse=True)
def _migrate_schema():
    """Build the schema with real Alembic migrations, mirroring CI's
    `alembic upgrade head` — never `Base.metadata.create_all`."""
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def db_session():
    """One real DB session per test, wired in as the `get_db` override.

    This is the single seam HANDOFF-02 (async migration) needs to touch.
    """
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    def _get_db_override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.pop(get_db, None)
        # Truncate everything so tests are order-independent. CASCADE handles
        # FK ordering; RESTART IDENTITY keeps id defaults sane (none of our
        # PKs are serial today, but this is cheap insurance).
        with engine.begin() as conn:
            tables = [t.name for t in Base.metadata.sorted_tables if t.name != "alembic_version"]
            if tables:
                conn.execute(text(f'TRUNCATE TABLE {", ".join(tables)} RESTART IDENTITY CASCADE'))


@pytest.fixture(autouse=True)
def _mock_external_io(monkeypatch):
    """Mock all external I/O per HANDOFF-01 guardrail: tests must never hit a
    real SMTP server, Cloudflare R2, Brankas, or Didit endpoint."""
    monkeypatch.setattr("app.auth.service.send_verification_email", lambda *a, **kw: None)
    monkeypatch.setattr("app.auth.service.send_password_reset_email", lambda *a, **kw: None)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# --------------------------------------------------------------------------- #
# Behavioral factory helpers. These call the real API wherever an endpoint
# exists. Two preconditions have no reachable endpoint at all (see comments
# below on approve_kyc_documents and make_admin) -- those use a direct ORM
# write (never raw SQL) purely as test setup, not as the behavior under test.
# --------------------------------------------------------------------------- #

DEFAULT_PASSWORD = "Str0ngPassw0rd!1"


@pytest.fixture
def make_user(client):
    """Register (+optionally self-select a role for) a user; return tokens/headers."""

    def _make(role: str | None = None, email: str | None = None, full_name: str = "Test User"):
        email = email or f"user-{uuid.uuid4().hex[:12]}@example.com"
        reg = client.post(
            "/auth/register",
            json={"email": email, "password": DEFAULT_PASSWORD, "full_name": full_name},
        )
        assert reg.status_code == 200, reg.text
        user_id = reg.json()["id"]

        login = client.post("/auth/login", json={"email": email, "password": DEFAULT_PASSWORD})
        assert login.status_code == 200, login.text
        access_token = login.cookies.get("access_token")
        refresh_token = login.cookies.get("refresh_token")
        headers = {"Authorization": f"Bearer {access_token}"}

        if role:
            role_resp = client.patch("/users/me/role", json={"role": role}, headers=headers)
            assert role_resp.status_code == 200, role_resp.text

        return {
            "id": user_id,
            "email": email,
            "password": DEFAULT_PASSWORD,
            "role": role,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "headers": headers,
        }

    return _make


def auth_headers(user: dict) -> dict:
    return user["headers"]


@pytest.fixture
def make_admin(make_user, db_session):
    """ADMIN is provisioned out-of-band per CLAUDE.md ("FL operations staff"),
    not self-selectable via /users/me/role (only SME/INVESTOR are). There is
    no admin-provisioning endpoint in scope for this suite, so this fixture
    registers a normal user through the real API and then promotes it with a
    direct ORM write -- the only way to reach that state today."""

    def _make(email: str | None = None):
        from app.users.models import User

        user = make_user(role=None, email=email)
        row = db_session.query(User).filter(User.id == user["id"]).first()
        row.role = "ADMIN"
        db_session.commit()
        return user

    return _make


@pytest.fixture
def make_project(client):
    def _make(sme: dict, legal_name: str | None = None, tax_id: str | None = None):
        legal_name = legal_name or f"Test Co {uuid.uuid4().hex[:8]}"
        tax_id = tax_id if tax_id is not None else f"TAX-{uuid.uuid4().hex[:10]}"
        resp = client.post(
            "/projects",
            json={"legal_name": legal_name, "tax_id": tax_id},
            headers=auth_headers(sme),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_loan_application(client):
    def _make(sme: dict, project_id: str, requested_amount: str = "100000.00"):
        resp = client.post(
            "/loans/applications",
            json={"business_id": project_id, "requested_amount": requested_amount},
            headers=auth_headers(sme),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def submit_loan_application(client):
    def _submit(sme: dict, application_id: str):
        return client.post(
            f"/loans/applications/{application_id}/submit",
            headers=auth_headers(sme),
        )

    return _submit


@pytest.fixture
def run_and_lock_score(client):
    """Start a score run (SUBMITTED -> UNDER_REVIEW, side effect on the
    application) and immediately lock it (READY -> LOCKED). Returns the
    score_run id."""

    def _run(admin: dict, application_id: str):
        start = client.post(
            "/underwriting/score-runs",
            json={"application_id": application_id, "mode": None},
            headers=auth_headers(admin),
        )
        assert start.status_code == 201, start.text
        score_run_id = start.json()["id"]
        approve = client.post(
            f"/underwriting/score-runs/{score_run_id}/approve",
            headers=auth_headers(admin),
        )
        assert approve.status_code == 200, approve.text
        return score_run_id

    return _run


@pytest.fixture
def make_contract(client):
    def _make(admin: dict, application_id: str, score_run_id: str):
        resp = client.post(
            "/contracts/",
            json={"application_id": application_id, "score_run_id": score_run_id},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def approve_kyc_documents(db_session):
    """Mark a project's KYC documents APPROVED so it can be listed.

    NOTE: there is no reachable API endpoint anywhere in the app that sets
    Document.status = "APPROVED" (verified by grepping the whole app/ tree).
    project_has_verified_kyc() therefore can never return True through the
    real API surface today -- this is a genuine gap, listed in the PR
    description for Edward to triage. This fixture uses a direct ORM insert
    (not raw SQL) purely as test setup for a precondition that has no service
    to call; it is not the behavior under test.
    """
    from app.lending.kyc import KYC_PURPOSES

    def _approve(project_id: str):
        for purpose in KYC_PURPOSES:
            db_session.add(
                Document(
                    entity_type="PROJECT",
                    entity_id=project_id,
                    purpose=purpose,
                    filename=f"{purpose}.pdf",
                    status="APPROVED",
                    storage_key=f"test/{project_id}/{purpose}.pdf",
                )
            )
        db_session.commit()

    return _approve


@pytest.fixture
def make_listing(client):
    def _make(admin: dict, contract_id: str, target_amount: str = "10000.00", min_ticket: str = "1000.00"):
        resp = client.post(
            "/market/listings",
            json={"contract_id": contract_id, "target_amount": target_amount, "min_ticket": min_ticket},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def place_order(client):
    def _place(investor: dict, listing_id: str, amount: str = "1000.00", idempotency_key: str | None = None,
               ack_risk_disclosure: bool = True):
        headers = dict(auth_headers(investor))
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return client.post(
            f"/market/listings/{listing_id}/orders",
            json={"amount": amount, "ackRiskDisclosure": ack_risk_disclosure},
            headers=headers,
        )

    return _place


@pytest.fixture
def open_listing(make_user, make_admin, make_project, make_loan_application, submit_loan_application,
                  run_and_lock_score, make_contract, approve_kyc_documents, make_listing):
    """End-to-end setup reaching an OPEN listing ready to accept orders:
    SME project -> submitted application -> scored & locked -> contract
    (ACTIVE_PENDING_FUNDING) -> KYC approved -> OPEN listing.

    Returns dict with sme, admin, project, application, contract, listing.
    """

    def _setup(target_amount: str = "10000.00", min_ticket: str = "1000.00"):
        sme = make_user(role="SME")
        admin = make_admin()
        project = make_project(sme)
        application = make_loan_application(sme, project["id"], requested_amount=target_amount)
        submit_resp = submit_loan_application(sme, application["id"])
        assert submit_resp.status_code == 200, submit_resp.text
        score_run_id = run_and_lock_score(admin, application["id"])
        contract = make_contract(admin, application["id"], score_run_id)
        approve_kyc_documents(project["id"])
        listing = make_listing(admin, contract["id"], target_amount=target_amount, min_ticket=min_ticket)
        return {
            "sme": sme,
            "admin": admin,
            "project": project,
            "application": application,
            "contract": contract,
            "listing": listing,
        }

    return _setup


@pytest.fixture
def funded_contract(open_listing, place_order, make_user):
    """Fully funds a listing (one order for the whole target_amount) so the
    contract reaches ACTIVE_FUNDED -- the precondition for disbursements and
    repayments. Returns the open_listing() dict plus "investor" and "order"."""

    def _setup(target_amount: str = "10000.00", min_ticket: str = "1000.00"):
        setup = open_listing(target_amount=target_amount, min_ticket=min_ticket)
        investor = make_user(role="INVESTOR")
        order_resp = place_order(investor, setup["listing"]["id"], amount=target_amount)
        assert order_resp.status_code == 201, order_resp.text
        setup["investor"] = investor
        setup["order"] = order_resp.json()
        return setup

    return _setup
