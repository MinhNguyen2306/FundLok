# HANDOFF-02 — Structural Fixes (branch off tested `main`)

> **For:** implementing model (Claude Sonnet)
> **From:** Edward (CTO) — architecture direction by Claude
> **Branch:** `structural-fixes` off `main` **after HANDOFF-01 (test suite) is merged**
> **Precondition:** the behavioral test suite from HANDOFF-01 is green on `main`. It is your regression guard for every change here.
> **Status:** ready once precondition met

---

## 0. The prime directive

These are **behavior-preserving refactors** (with one deliberate behavior change — token revocation, §2). The HANDOFF-01 suite must stay green throughout. If a refactor turns a test red, either the refactor is wrong or the behavior change is intentional — and if intentional, you update the test *and say so in the PR*. A silently rewritten test is a failure.

Work each fix as its own commit (ideally its own PR stacked on the branch) so review is bisectable: async layer → token revocation → module cleanup.

---

## 1. Fix A — Async DB layer (sync SQLAlchemy → async)

### Current state
- `app/core/database.py` uses `create_engine` + `sessionmaker` + a sync `get_db()` generator.
- Driver is `psycopg2` (see `requirements.txt`, `DATABASE_URL` uses `postgresql+psycopg2://...` in CI).
- Every service and router depends on sync `Session` and `db.query(...)`. Grep confirms `Session` type hints across `app/**` (auth, loans, payments, contracts, projects, market, underwriting, `app/utils/jwt.py`, `app/main.py`).
- `CLAUDE.md` already declares the target: "All DB operations use `AsyncSession`. Never use sync `Session` in V2 code."

### Target
- `app/core/database.py`: `create_async_engine` + `async_sessionmaker(expire_on_commit=False)` + `async def get_db()` yielding `AsyncSession`.
- Driver → `asyncpg`. Add `asyncpg` and `sqlalchemy[asyncio]` to `requirements.txt`; app `DATABASE_URL` becomes `postgresql+asyncpg://...`.
- Convert every DB-touching function to `async def` and every query to the 2.x async style: `await db.execute(select(Model).where(...))` then `.scalar_one_or_none()` / `.scalars().all()`. Replace `db.query(...)`, `.first()`, `.all()` accordingly.
- `await db.commit()` / `await db.flush()` / `await db.refresh(obj)` everywhere they were sync.
- `app/utils/jwt.py::get_current_user` → `async def`, `AsyncSession`, `await db.execute(select(User)...)`.
- `app/main.py::test_db` → async.

### Alembic — keep it sync
Do **not** convert Alembic to async. `alembic/env.py` uses `create_engine` and that is fine and standard. Alembic keeps its own sync URL (`postgresql+psycopg2://...`); the app uses the async URL. Two URLs, one for migrations, one for the app. This avoids destabilizing the migration-check CI job. Keep `psycopg2-binary` in requirements for Alembic.

### CI
- The app's `DATABASE_URL` for the test run becomes async (`+asyncpg`). The `migration-check` job's `DATABASE_URL` stays `+psycopg2`. Set them independently per job — do not force one URL for both.
- The HANDOFF-01 test fixtures assume an async session after this fix: the `get_db` override in `conftest.py` (the single seam called out in HANDOFF-01 §4) must now yield an `AsyncSession`, and tests use `httpx.AsyncClient` + `pytest-asyncio`. Add `pytest-asyncio` to requirements. This is the expected, isolated test change.

### Gotchas
- `expire_on_commit=False` on the session maker, or accessing attributes after commit will trigger lazy IO and blow up.
- No lazy-loaded relationship access outside a session in async — use eager loading (`selectinload`) where a response serializes related rows.
- `BackgroundTasks` is imported in `app/main.py`; per `CLAUDE.md`, financial background work must go through ARQ, not `BackgroundTasks`. Do not add new `BackgroundTasks` usage; leave existing non-financial usage unless it blocks the async conversion.

### Acceptance
- All HANDOFF-01 tests pass against the async stack (converted to async client as above).
- No sync `Session` import remains in `app/**` (grep clean). `alembic check` still passes.

---

## 2. Fix B — DB-backed refresh token revocation (deliberate behavior change)

### Current state
- `app/auth/service.py::create_token_pair` issues a **stateless** refresh JWT and explicitly notes it bypasses the DB: *"refresh tokens are stateless JWTs for MVP robustness… avoids DB dependencies when `refresh_tokens` table can't be created/altered."*
- `refresh_token_pair` decodes and re-issues without any server-side check. `logout` (`app/auth/router.py`) only deletes the cookie — a stolen refresh token remains valid until expiry.
- **The model already exists:** `app/users/models.py::RefreshToken` (`refresh_tokens` table) with `id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at`, and a `User.refresh_tokens` relationship. It is modeled but there is **no migration creating the table** (that is what the comment means by "can't be created").

### Target
Make refresh tokens stateful and revocable, using the existing model.

1. **Migration** — add the next sequential migration (`0006_create_refresh_tokens.py` per `CLAUDE.md` naming) that creates the `refresh_tokens` table exactly matching the `RefreshToken` model. UUID PK, `TIMESTAMPTZ` columns, FK to `users.id` with `ON DELETE CASCADE`, unique index on `token_hash`. Do not touch frozen migrations `0001`–`0003`.
2. **Issue** — `create_token_pair`: on issuing a refresh token, persist a `RefreshToken` row storing a **hash** of the token (never the raw token), with `expires_at`. Store `token_hash` = a strong hash (reuse the hashing approach in `app/utils/password.py` or a SHA-256 of the token — pick one, document it).
3. **Verify + rotate** — `refresh_token_pair`: after JWT signature/expiry checks, look up the row by `token_hash`; reject if missing, `revoked_at IS NOT NULL`, or past `expires_at`. On success, **revoke the presented token** (set `revoked_at = now()`) and insert a new row for the rotated token. This is proper rotation with reuse detection.
4. **Logout** — `app/auth/router.py::logout`: set `revoked_at = now()` on the presented refresh token's row (in addition to clearing the cookie).
5. Remove the "stateless for MVP" comments once the DB path is live.

### Behavior change is expected
The HANDOFF-01 refresh/logout tests characterized the *old stateless* behavior. Update them here to assert the new behavior:
- `test_logout_revokes_refresh_token_server_side` — after logout, the same refresh token is rejected on `/refresh`.
- `test_reused_refresh_token_after_rotation_is_rejected` — using a rotated-away token fails.
- `test_refresh_token_hash_not_stored_in_plaintext` — the stored value is a hash, not the raw token.
Call these test changes out explicitly in the PR description so review knows they are intentional, not accidental regressions.

### Acceptance
- Migration applies cleanly; `alembic check` passes.
- Stolen/rotated/logged-out refresh tokens are rejected server-side.
- Raw refresh tokens never persisted.

---

## 3. Fix C — Module cleanup (`app/files/` → `app/uploads/`)

### Current state
Both `app/files/` and `app/uploads/` exist with parallel `router.py` / `service.py` / `schemas.py`. `app/main.py` includes **both** `files_router` and `uploads_router`. `CLAUDE.md` (Phase 0) says: "merge `app/files/` into `app/uploads/`."

### Ownership caution
`app/uploads/` and `app/files/` are in **Phat's** ownership column (`CLAUDE.md`). This cleanup touches UI-integrated endpoints. **Do not proceed on this fix without Phat's sign-off on the endpoint surface**, because it can change routes the frontend calls. Recommended: land Fix A and Fix B first; open Fix C as a separate PR that Phat reviews. If any route path/response the frontend depends on would change, that is a contract change and must be agreed before merge.

### Target
- Merge `app/files/` functionality into `app/uploads/`, preserving the existing external route paths and response schemas (no contract break) unless Phat approves a change.
- Remove `app/files/` and its `files_router` include from `app/main.py`.
- Update any imports referencing `app.files`.

### Acceptance
- No duplicate upload modules; `app/files/` gone.
- All HANDOFF-01 upload/behavioral tests still green; no unreviewed route/schema change.
- Phat has approved the endpoint surface.

---

## 4. Explicitly OUT of scope for this handoff

These are Phase-0 / V2 items but do **not** belong in the structural-fixes branch — they are net-new feature work, not behavior-preserving refactors:
- ARQ worker scaffold
- Ledger immutability DB trigger (comes with the banking/ledger V2 work)
- Any `app/banking/`, `app/repayment_schedule/`, `app/share_conversion/`, `app/compliance/` module
- Omnibus vs. escrow account modeling (pending ADR-003 — see below)

Keeping this branch to async + tokens + cleanup keeps it reviewable and keeps the test suite meaningful as a guard.

---

## 5. Definition of done

- Branch `structural-fixes` cut from a `main` that already has the HANDOFF-01 suite.
- Fixes A and B complete; Fix C complete or split into its own Phat-reviewed PR.
- Full test suite green in CI (both `migration-check` and `tests` jobs).
- No sync `Session` left in `app/**`. `alembic check` passes.
- PR descriptions link this handoff and flag every intentional test change.

---

## 6. Note for Edward (not for Sonnet)

Sequencing after this branch merges: V2 work on the internal ledger begins. Per our discussion, the plan is **omnibus-first with an escrow-compatible seam** — every `bank_transaction` and balance snapshot references a `custodial_account` (one row under omnibus; one per contract under escrow), and no platform-wide netting is assumed. That decision should be recorded as **ADR-003** before the `app/banking/` spec is written, so Phat and future sessions inherit the constraint. ADR-002 stays as-is (partner still TBD).
