# HANDOFF-01 — Behavioral Test Suite (run against `main`)

> **For:** implementing model (Claude Sonnet)
> **From:** Edward (CTO) — architecture direction by Claude
> **Branch:** `test-suite` off `main` → PR → merge to `main` **before** any structural work begins
> **Status:** ready to implement
> **Do NOT** start HANDOFF-02 (structural fixes) until this is merged.

---

## 1. Why this exists (read before coding)

FundLok is about to migrate the DB layer from **sync SQLAlchemy → async** (HANDOFF-02). That is a behavior-preserving refactor of the riskiest kind: it rewrites how every endpoint talks to the database. Without a test suite that captures **current** behavior, we cannot prove the async version still behaves identically.

So this suite is a **characterization / golden-master suite**: it documents what `main` does *today* and becomes the regression guard for the async migration and every structural fix after it.

There is currently **no `tests/` directory and no `conftest.py`**. `pytest` and `httpx` are already in `requirements.txt`. CI (`.github/workflows/ci.yml`) runs only `alembic upgrade` + `alembic check` — no test step yet.

---

## 2. The one rule that makes this suite survive the async migration

**Test behavior, not implementation.** Write tests at two levels only:

- **HTTP/endpoint level** — spin up the FastAPI app, hit routes with `httpx`, assert on status codes, response bodies, and state transitions.
- **Service level as black boxes** — call service functions with their inputs, assert on returns and persisted rows.

**Do NOT** assert on sync-specific mechanics: no reaching into `Session` internals, no asserting on `db.query(...)` call shapes, no coupling to `sessionmaker`/`Engine` objects. If a test knows the DB layer is sync, it will break during the async swap for the wrong reason and prove nothing. Written behaviorally, the *same* test file must pass on sync `main` today and pass again after HANDOFF-02.

---

## 3. Scope — what to characterize

Cover the existing behavior in `app/` as it stands on `main`. Priority order:

1. **Health & DB connectivity** — `GET /health`, `GET /test-db` (both defined in `app/main.py`).
2. **Auth lifecycle** (`app/auth/router.py`, `app/auth/service.py`):
   - register → login → access protected route → refresh → logout
   - login with bad credentials → 401
   - refresh with a non-refresh / tampered / expired token → 401
   - **Document current behavior as-is:** refresh tokens are currently *stateless JWTs* (`create_token_pair` in `app/auth/service.py` bypasses the `refresh_tokens` table on purpose). Assert what it does now. HANDOFF-02 changes this behavior deliberately and will update these tests — that is expected and is exactly the signal we want.
3. **RBAC** (`app/utils/rbac.py`, roles `SME` / `INVESTOR` / `ADMIN`) — a route requiring one role rejects the others with 403.
4. **Lending state transitions** (models in `app/lending/models.py`) — cover the transitions in the state machine that are reachable via the API:
   - `LoanApplication: DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED|REJECTED`
   - `Order: PENDING_PAYMENT → FILLED|CANCELLED|EXPIRED`
   - `Contract` and `Listing` transitions where an endpoint drives them.
5. **Idempotency — highest value, do not skip:**
   - `Order` has a unique `idempotency_key` (`app/lending/models.py`, migration `0002`). Posting the same `Idempotency-Key` twice must create **one** row and return the existing record on the second call.
   - `LedgerEntry` has a unique `idempotency_key` (migration `0003`). Same guarantee. This is the mechanism that will make Brankas at-least-once webhooks safe in V2, so lock its current behavior down now.
6. **Ledger append-only invariant** — assert the service layer only ever inserts into `ledger_entries` (no UPDATE/DELETE path is exposed). A test that attempts to mutate a ledger entry through the app surface should find no such route.

Out of scope: React frontend (Phat owns), external R2/Brankas calls (mock them), email delivery, load/perf.

---

## 4. Test infrastructure to build

```
tests/
  conftest.py            # fixtures: test app, test DB, client, auth helpers
  test_health.py
  auth/test_auth_lifecycle.py
  auth/test_refresh_and_logout.py
  rbac/test_role_enforcement.py
  lending/test_loan_application_state.py
  lending/test_order_state.py
  lending/test_idempotency_orders.py
  lending/test_idempotency_ledger.py
  lending/test_ledger_append_only.py
```

**Fixtures (`conftest.py`):**
- A test Postgres DB (mirror CI: `postgres:15` service). Run `alembic upgrade head` against it in a session-scoped fixture so the schema matches production migrations — **do not** create tables from `Base.metadata` directly (that would hide migration drift, which `alembic check` is there to catch).
- Override the `get_db` dependency (`app/core/database.py`) to yield a session bound to the test DB. **Note for HANDOFF-02:** this override is the single seam the async migration will touch in tests — keep it isolated in `conftest.py` so the migration only edits one fixture, not every test.
- Function-scoped transaction rollback (or truncate) between tests so tests are independent and order-agnostic.
- Factory helpers: `make_user(role=...)`, `auth_headers(user)`, `make_loan_application(...)`, etc. Keep these behavioral — they call the real API or real services, not raw SQL where avoidable.

---

## 5. Acceptance criteria (these become the test function names)

Binary and testable. Sonnet: name your test functions to match.

- `test_health_returns_healthy`
- `test_test_db_reports_connected`
- `test_register_then_login_issues_token_pair`
- `test_login_with_bad_password_returns_401`
- `test_access_protected_route_with_valid_token_succeeds`
- `test_access_protected_route_without_token_returns_401`
- `test_refresh_with_valid_refresh_token_returns_new_pair`
- `test_refresh_with_access_token_typ_rejected`
- `test_refresh_with_tampered_token_returns_401`
- `test_logout_clears_refresh_cookie`
- `test_role_protected_route_rejects_wrong_role_403`
- `test_loan_application_draft_to_submitted`
- `test_loan_application_submitted_to_approved_and_rejected_paths`
- `test_order_pending_to_filled`
- `test_order_cannot_transition_from_terminal_state`
- `test_duplicate_idempotency_key_on_order_returns_existing_row`
- `test_duplicate_idempotency_key_on_ledger_entry_returns_existing_row`
- `test_ledger_entry_has_no_exposed_mutation_route`

Add more as you discover reachable behavior — but every one must be a black-box assertion.

---

## 6. CI change

Add a `tests` job to `.github/workflows/ci.yml` that runs alongside the existing `migration-check` job:

- Same `postgres:15` service and env vars already defined in that file.
- Steps: checkout → setup Python 3.11 → `pip install -r requirements.txt` → `alembic upgrade head` → `pytest -q`.
- Make the PR gate require both jobs green.

Do not modify the existing `migration-check` job.

---

## 7. Guardrails

- **Characterize, don't fix.** If a test reveals a real bug in `main`, do **not** silently change app logic to make the test pass. Write the test to assert *actual current behavior*, and open a separate note/issue listing the bug. Edward decides whether the fix lands on `main` (as its own small PR) before the `structural-fixes` branch is cut — per the agreed sequencing.
- No schema changes. Migrations `0001`–`0003` (and existing hash-named ones) are frozen.
- No changes to any `app/` business logic in this PR. This PR adds `tests/`, `conftest.py`, and the CI job **only**.
- Mock all external I/O (Cloudflare R2, Brankas, email). Tests must never hit a real external service.

---

## 8. Definition of done

- `pytest -q` passes locally and in CI against `main`.
- Every acceptance-criterion test in §5 exists and passes (or is documented as an intentional known-bug assertion).
- No `app/` logic changed; diff is `tests/**`, `conftest.py`, `requirements.txt` (if a test-only dep is added), and `.github/workflows/ci.yml`.
- PR description links this handoff and lists any bugs surfaced.
- Merged to `main`. → **Then** cut `structural-fixes` off the updated `main` and start HANDOFF-02.
