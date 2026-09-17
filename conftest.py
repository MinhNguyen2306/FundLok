"""Shared pytest fixtures for the FundLok behavioral test suite.

Originally built for HANDOFF-01 (see docs/handoffs/HANDOFF-01-test-suite.md);
updated for HANDOFF-02 Fix A (docs/handoffs/HANDOFF-02-structural-fixes.md),
which moved the app from sync SQLAlchemy to async. Per HANDOFF-01 §4, the
`get_db` override was kept isolated to this one fixture specifically so this
migration only had to touch one seam -- it did.

Design constraints:
- Schema comes from real Alembic migrations (`alembic upgrade head`) against a
  throwaway Postgres, never from `Base.metadata.create_all` — that would hide
  migration drift that `alembic check` exists to catch. Alembic itself stays
  on a sync psycopg2 URL (HANDOFF-02 Fix A) even though the app/tests are
  async, so this file derives a separate sync URL just for that migration
  step.
- Tests are isolated by truncating all tables between tests (not per-test
  transactions), because some app code opens its own session outside of
  `get_db` (e.g. app.system.service.is_maintenance_active uses SessionLocal()
  directly), which would not see an uncommitted outer transaction.
- All external I/O (email, R2, Brankas, Didit, Turnstile) is mocked/disabled.
- Async: test functions are plain `async def` (pytest.ini sets
  asyncio_mode = auto) and the HTTP client is httpx.AsyncClient over the
  ASGI app directly, per HANDOFF-02 Fix A.
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
    "postgresql+asyncpg://test_user:test_password@localhost:5432/test_db",
)
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
# A real Fernet key, so the TOTP tests exercise the encrypted path rather than a
# bypass. Deliberately NOT derived from SECRET_KEY — see app/auth/totp_crypto.py
# for why the two secrets are separate.
os.environ.setdefault("TOTP_ENCRYPTION_KEY", "n5W7jlQOzlCKwRHfeCH4cpb6vUvai3kOX0GnEgEh9i4=")
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

from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker  # noqa: E402

from app.core.base import Base  # noqa: E402
from app.core.database import engine, get_db  # noqa: E402
from app.lending.models import Document  # noqa: E402
from app.main import app  # noqa: E402
from app.users.models import RefreshToken, User  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
# Alembic intentionally stays on a sync driver (HANDOFF-02 Fix A) -- derive
# its own psycopg2 URL from whatever async URL the app/tests are using,
# rather than requiring a second env var. A no-op .replace() if DATABASE_URL
# is already a sync URL.
ALEMBIC_DATABASE_URL = TEST_DATABASE_URL.replace("+asyncpg", "+psycopg2")
ALEMBIC_COMMAND = [sys.executable, "-m", "alembic"]


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
    `alembic upgrade head` — never `Base.metadata.create_all`.

    This intentionally shells out to `alembic upgrade head` as a subprocess
    (exactly like the CI "tests" job's dedicated migration step) rather than
    calling alembic's Python API in-process. alembic/env.py reads
    `settings.DATABASE_URL` directly (not the Config object's
    `sqlalchemy.url`, which command.upgrade()'s in-process API would let us
    override) -- and `settings` is a module-level singleton already
    constructed with the asyncpg URL by the time this fixture runs. A
    subprocess gets its own fresh `settings` from the env we pass it, which
    is the only way to hand Alembic a sync psycopg2 URL while the rest of the
    suite runs against the async one.
    """
    import subprocess

    env = {**os.environ, "DATABASE_URL": ALEMBIC_DATABASE_URL}
    result = subprocess.run(
        [*ALEMBIC_COMMAND, "upgrade", "head"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"alembic upgrade head failed (exit {result.returncode}):\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    yield


@pytest.fixture(autouse=True)
async def db_session():
    """One real AsyncSession per test, wired in as the `get_db` override.

    This is the single seam HANDOFF-01 called out and HANDOFF-02's async
    migration touched.
    """
    TestingSessionLocal = async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()

    async def _get_db_override():
        yield session

    app.dependency_overrides[get_db] = _get_db_override
    try:
        yield session
    finally:
        app.dependency_overrides.pop(get_db, None)
        # Truncate everything so tests are order-independent. CASCADE handles
        # FK ordering; RESTART IDENTITY keeps id defaults sane (none of our
        # PKs are serial today, but this is cheap insurance).
        #
        # Deliberately reuses THIS session/connection rather than checking
        # out a fresh one from the pool: doing the truncate on a second
        # connection immediately after closing this one raced against
        # asyncpg's own connection-reset bookkeeping (observed as
        # "InterfaceError: cannot perform operation: another operation is in
        # progress" during fixture teardown). rollback() first clears any
        # leftover implicit transaction/aborted state from whatever the test
        # did (e.g. a request that ended in an HTTPException).
        await session.rollback()
        # `custodial_accounts` is excluded alongside `alembic_version`: the
        # ledger-foundation migration seeds exactly one scope='PLATFORM' row
        # as fixed reference data (ADR-003), not per-test state -- truncating
        # it here would silently delete that seed after the first test and
        # break every subsequent resolve_custodial_account() call. Tables
        # that reference it (ledger_accounts, ledger_entries, ...) are still
        # truncated normally.
        #
        # `bank_rate_config` is excluded for the identical reason (T0b): the
        # score-run-persistence migration seeds exactly one board rate
        # (12.0%, effective 2026-09-17) as fixed reference data. Found by
        # actually running this suite against real Postgres (T4, HANDOFF-03)
        # -- every score-run test after the first failed with "no
        # bank_rate_config row is in force" once the seed row was truncated
        # away, because `bank_rate_config.created_by_actor_id` is a FK into
        # `users`, and CASCADE follows that FK the same way it follows
        # `custodial_accounts.contract_id` into `contracts` below.
        tables = [
            t.name
            for t in Base.metadata.sorted_tables
            if t.name not in ("alembic_version", "custodial_accounts", "bank_rate_config")
        ]
        if tables:
            await session.execute(text(f'TRUNCATE TABLE {", ".join(tables)} RESTART IDENTITY CASCADE'))
            # Excluding `custodial_accounts` from the TRUNCATE list above
            # isn't sufficient on its own: `custodial_accounts.contract_id`
            # is a FK to `contracts.id`, and Postgres's TRUNCATE ... CASCADE
            # truncates *every* table with a FK into any table named in the
            # statement -- so truncating `contracts` (correctly, per-test
            # data) cascades into `custodial_accounts` too and wipes the
            # seeded PLATFORM row regardless. Re-seed it idempotently so it
            # survives every test, the same way the migration provisions it
            # once for a real environment.
            await session.execute(
                text(
                    "INSERT INTO custodial_accounts (scope, status) "
                    "SELECT 'PLATFORM', 'ACTIVE' "
                    "WHERE NOT EXISTS (SELECT 1 FROM custodial_accounts WHERE scope = 'PLATFORM')"
                )
            )
            # `bank_rate_config` gets the same CASCADE-from-`users` treatment
            # as `custodial_accounts`, but unlike that idempotent
            # insert-if-missing, this resets to exactly the migration's one
            # baseline row every test: a test that calls set_bank_rate()
            # (T0b's rate-history-is-append-only design means those rows
            # would otherwise accumulate across tests and leak into
            # `get_current_bank_rate()` in a later, unrelated test).
            await session.execute(text("TRUNCATE TABLE bank_rate_config RESTART IDENTITY CASCADE"))
            await session.execute(
                text(
                    "INSERT INTO bank_rate_config (id, rate_pct, effective_from) "
                    "VALUES (gen_random_uuid(), 12.0, '2026-09-17')"
                )
            )
            await session.commit()
        await session.close()


@pytest.fixture(autouse=True)
def _mock_external_io(monkeypatch):
    """Mock all external I/O per HANDOFF-01 guardrail: tests must never hit a
    real SMTP server, Cloudflare R2, Brankas, or Didit endpoint."""
    monkeypatch.setattr("app.auth.service.send_verification_email", lambda *a, **kw: None)
    monkeypatch.setattr("app.auth.service.send_password_reset_email", lambda *a, **kw: None)
    monkeypatch.setattr("app.auth.service.send_existing_account_notice", lambda *a, **kw: None)
    # Imported into two modules, so it needs stubbing at both call sites. A
    # test that asserts on the notice re-patches the same target itself; this
    # autouse fixture runs first, so the test's own monkeypatch still wins.
    monkeypatch.setattr("app.auth.service.send_password_changed_notice", lambda *a, **kw: None)
    monkeypatch.setattr("app.users.service.send_password_changed_notice", lambda *a, **kw: None)

    # Backstop under all of the above. Patching senders one call site at a
    # time is a list that silently goes stale -- send_password_changed_notice
    # was added to two modules and to neither list, and the gap only surfaced
    # in CI, because a developer machine has mailpit on :1025 (ADR-005) and
    # quietly accepts the mail. Every sender in app/utils/email.py bottoms out
    # here, so a new one can no longer reach the network just by being
    # forgotten.
    monkeypatch.setattr("app.utils.email.send_email", lambda *a, **kw: None)

    # GVerify verification-document retention writes to R2 — never in tests.
    async def _no_store(*a, **kw):
        return None

    monkeypatch.setattr("app.gverify.storage.store_kyc_documents", _no_store)
    monkeypatch.setattr("app.gverify.storage.store_kyb_document", _no_store)
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


# --------------------------------------------------------------------------- #
# Behavioral factory helpers. These call the real API wherever an endpoint
# exists. Two preconditions have no reachable endpoint at all (see comments
# below on approve_kyc_documents and make_admin) -- those use a direct ORM
# write (never raw SQL) purely as test setup, not as the behavior under test.
# All of these are async closures now (HANDOFF-02): callers must `await` them.
# --------------------------------------------------------------------------- #

DEFAULT_PASSWORD = "Str0ngPassw0rd!1"


@pytest.fixture
def make_user(client):
    """Register (+optionally self-select a role for) a user; return tokens/headers."""

    async def _make(role: str | None = None, email: str | None = None, full_name: str = "Test User"):
        email = email or f"user-{uuid.uuid4().hex[:12]}@example.com"
        reg = await client.post(
            "/auth/register",
            json={"email": email, "password": DEFAULT_PASSWORD, "full_name": full_name},
        )
        # Register returns a uniform ack (no user body, 201) so it can't be used
        # to enumerate accounts; the user id comes from the login response.
        assert reg.status_code == 201, reg.text

        login = await client.post("/auth/login", json={"email": email, "password": DEFAULT_PASSWORD})
        assert login.status_code == 200, login.text
        user_id = login.json()["id"]
        access_token = login.cookies.get("access_token")
        refresh_token = login.cookies.get("refresh_token")
        headers = {"Authorization": f"Bearer {access_token}"}

        if role:
            role_resp = await client.patch("/users/me/role", json={"role": role}, headers=headers)
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

    async def _make(email: str | None = None):
        user = await make_user(role=None, email=email)
        result = await db_session.execute(select(User).where(User.id == user["id"]))
        row = result.scalar_one()
        row.role = "ADMIN"
        await db_session.commit()
        return user

    return _make


@pytest.fixture
def make_project(client):
    async def _make(sme: dict, legal_name: str | None = None, tax_id: str | None = None):
        legal_name = legal_name or f"Test Co {uuid.uuid4().hex[:8]}"
        tax_id = tax_id if tax_id is not None else f"TAX-{uuid.uuid4().hex[:10]}"
        resp = await client.post(
            "/projects",
            json={"legal_name": legal_name, "tax_id": tax_id},
            headers=auth_headers(sme),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_loan_application(client):
    async def _make(sme: dict, project_id: str, requested_amount: str = "100000.00"):
        resp = await client.post(
            "/loans/applications",
            json={"business_id": project_id, "requested_amount": requested_amount},
            headers=auth_headers(sme),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def submit_loan_application(client):
    async def _submit(sme: dict, application_id: str):
        return await client.post(
            f"/loans/applications/{application_id}/submit",
            headers=auth_headers(sme),
        )

    return _submit


@pytest.fixture
def run_and_lock_score(client):
    """Start a score run (SUBMITTED -> UNDER_REVIEW, side effect on the
    application) and immediately lock it (READY -> LOCKED). Returns the
    score_run id."""

    async def _run(admin: dict, application_id: str):
        start = await client.post(
            "/underwriting/score-runs",
            json={"application_id": application_id, "mode": None},
            headers=auth_headers(admin),
        )
        assert start.status_code == 201, start.text
        score_run_id = start.json()["id"]
        approve = await client.post(
            f"/underwriting/score-runs/{score_run_id}/approve",
            headers=auth_headers(admin),
        )
        assert approve.status_code == 200, approve.text
        return score_run_id

    return _run


@pytest.fixture
def make_contract(client):
    async def _make(admin: dict, application_id: str, score_run_id: str):
        resp = await client.post(
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

    async def _approve(project_id: str):
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
        await db_session.commit()

    return _approve


@pytest.fixture
def make_listing(client):
    async def _make(admin: dict, contract_id: str, target_amount: str = "10000.00", min_ticket: str = "1000.00"):
        resp = await client.post(
            "/market/listings",
            json={"contract_id": contract_id, "target_amount": target_amount, "min_ticket": min_ticket},
            headers=auth_headers(admin),
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def place_order(client):
    async def _place(investor: dict, listing_id: str, amount: str = "1000.00", idempotency_key: str | None = None,
                      ack_risk_disclosure: bool = True):
        headers = dict(auth_headers(investor))
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return await client.post(
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

    async def _setup(target_amount: str = "10000.00", min_ticket: str = "1000.00"):
        sme = await make_user(role="SME")
        admin = await make_admin()
        project = await make_project(sme)
        application = await make_loan_application(sme, project["id"], requested_amount=target_amount)
        submit_resp = await submit_loan_application(sme, application["id"])
        assert submit_resp.status_code == 200, submit_resp.text
        score_run_id = await run_and_lock_score(admin, application["id"])
        contract = await make_contract(admin, application["id"], score_run_id)
        await approve_kyc_documents(project["id"])
        listing = await make_listing(admin, contract["id"], target_amount=target_amount, min_ticket=min_ticket)
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

    async def _setup(target_amount: str = "10000.00", min_ticket: str = "1000.00"):
        setup = await open_listing(target_amount=target_amount, min_ticket=min_ticket)
        investor = await make_user(role="INVESTOR")
        order_resp = await place_order(investor, setup["listing"]["id"], amount=target_amount)
        assert order_resp.status_code == 201, order_resp.text
        setup["investor"] = investor
        setup["order"] = order_resp.json()
        return setup

    return _setup


@pytest.fixture
def get_refresh_token_row(db_session):
    """HANDOFF-02 Fix B test helper: look up a user's RefreshToken row(s)
    directly, to assert on hashing/revocation state that isn't visible via
    the API surface."""

    async def _get(user_id: str, *, token_hash: str | None = None):
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        if token_hash is not None:
            stmt = stmt.where(RefreshToken.token_hash == token_hash)
        stmt = stmt.order_by(RefreshToken.created_at.desc())
        result = await db_session.execute(stmt)
        return result.scalars().all()

    return _get
