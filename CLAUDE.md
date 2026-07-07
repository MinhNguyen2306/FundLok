# FundLok — Claude Session Bootstrap

> Read this file at the start of every session. It is the single source of truth for project context.
> Last updated: July 2026 | Version: 1.2

---

## What FundLok Is

FundLok (FL) is a Vietnam-registered P2P lending platform connecting SMB borrowers with lenders.

- **FL does NOT take a position.** It is a marketplace — it matches borrowers and lenders only.
- **Revenue model:** FL charges a fee percentage deducted from each disbursement/distribution, processed through the omnibus account.
- **Omnibus/custodial account:** FL holds a custodial account at a licensed Vietnamese bank. All fund movements (lender → FL, FL → borrower, borrower → FL, FL → lender) flow through this account. The Open API middleware is partner-TBD (a Brankas-style aggregator or the custodial bank direct). Per ADR-003, the ledger is built omnibus-first but escrow-compatible in case only a per-project escrow account can be signed.
- **Ledger:** FL maintains an internal append-only ledger that mirrors every bank movement. The ledger is the legal record. It is immutable at both the application layer and the database layer (PostgreSQL trigger).
- **Borrower journey:** SMB registers → 3rd-party KYC → describes project/enterprise → applies for loan → ML grading engine assigns interest rate tier → listed on marketplace → lenders fund → disbursement → scheduled repayments → lenders receive pro-rata distributions + converted shares after repayment.
- **Early repayment** is encouraged as a platform value — better practice, better outcomes.
- **Regulatory framework:** Vietnam Decree No. 94/2025/ND-CP (fintech/P2P regulatory sandbox) and Circular 64/2024/TT-NHNN (banking Open API technical standard). See ADR-004.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11, FastAPI |
| Database | PostgreSQL (SQLAlchemy 2.x async, Alembic migrations) |
| File storage | Cloudflare R2 (S3-compatible) |
| Auth | JWT (access + refresh), Argon2 password hashing, Google OAuth |
| Banking | Open API — custodial partner TBD (Brankas aggregator or direct bank); must meet Circular 64 (OAuth2, TLS 1.2+, ISO 20022) |
| Frontend | React (Phat owns — Edward does not touch UI) |
| Deployment | Docker, Google Cloud Run |
| CI/CD | GitHub Actions |
| Worker | ARQ (async task queue for ML scoring and scheduled jobs) |

---

## Architecture Decision: Modify, Not Rebuild

The MVP codebase (`/app`) is being extended, not rebuilt. See `docs/adr/001-modify-not-rebuild.md`.

Key carry-forwards:
- All 12 ORM models in `app/lending/models.py` and `app/users/models.py`
- Lending state machine (loans, contracts, market, payments services)
- Idempotency key pattern on `orders` and `ledger_entries`
- Alembic migration history is frozen — never alter existing migrations. Only `0001_initial_schema.py` uses a numeric name; all later migrations use Alembic hash-based revision IDs (e.g. `a7c4f1e2d3b5`). `0001` already contains the `orders`/`ledger_entries` idempotency columns **and** the `refresh_tokens` table. (The old numeric `0002`/`0003` idempotency files were redundant duplicates of columns already in `0001` and have been removed.)
- Auth, RBAC, Cloudflare R2 integration, CI/CD

---

## Module Ownership

**Ownership is strict. Do not modify files outside your boundary without explicit agreement.**

### Edward (CTO) — Backend, Architecture, Compliance
- `app/banking/` — Brankas API client, omnibus account service, webhook handlers
- `app/underwriting/` — ML grading engine (async)
- `app/repayment_schedule/` — amortization engine, early repayment tracking
- `app/share_conversion/` — post-repayment share issuance
- `app/compliance/` — Decree 94 reporting, exposure cap enforcement
- `app/ledger/` — double-entry ledger, custodial/ledger accounts, balance-by-sum (see ADR-003, docs/specs/ledger/ledger-foundation.md)
- `app/core/` — database session, config, async migration
- `app/utils/` — shared utilities (jwt, rbac, audit, r2, password)
- `alembic/` — all migrations
- `docs/adr/` — all Architecture Decision Records
- `docs/specs/` — all feature specs (Edward writes backend specs; Phat writes frontend specs)

### Phat — Full Stack + Sole Frontend Owner
- All React frontend (Edward does not touch UI under any circumstances)
- `app/users/router.py`, `app/users/schemas.py` — user-facing endpoints
- `app/projects/` — project management endpoints
- `app/loans/` — loan application endpoints
- `app/market/` — marketplace listing and order endpoints
- `app/sme/` — SME-specific flows
- `app/uploads/` — document upload endpoints (UI-integrated)
- `app/contact/` — contact/support endpoints
- `app/oauth/` — OAuth flows (frontend-facing)
- `app/admin/` — admin panel endpoints

### Shared (requires both to agree before changing)
- `app/models/__init__.py` — model re-exports
- `app/lending/models.py`, `app/users/models.py` — ORM models (schema changes via Alembic only)
- `app/auth/` — authentication core
- API contracts (OpenAPI schema) — defined in specs before either side implements

---

## Workflow: Spec-Driven Development

Every feature follows this sequence. No exceptions.

```
1. SPEC      Write spec in docs/specs/<module>/<feature>.md
2. REVIEW    Other engineer reviews spec (async, via PR comment)
3. CONTRACT  Agree on API contract (request/response types) before any code
4. BUILD     Implement against the spec — backend and frontend can work in parallel
5. TEST      Acceptance criteria in the spec become the test cases
6. ADR       If an architectural decision was made, record it in docs/adr/
```

**The spec is the handoff document.** If Phat picks up a spec written by Edward, he should need zero additional verbal/chat context to implement the frontend against it. If he does, the spec is incomplete — fix the spec, not the conversation.

**AI context rule:** Neither Claude nor Antigravity reliably carries context between sessions. All decisions, rationale, and conventions must be in the repo. If it is not written down, it does not exist.

---

## Spec Format

All specs live in `docs/specs/<module>/<feature>.md`. See `docs/specs/_TEMPLATE.md` for the required structure. Required sections:

1. Context & Goal
2. Out of Scope
3. Data Model (typed)
4. API Contract
5. State Machine (if applicable)
6. Business Rules
7. Error Cases
8. Acceptance Criteria
9. Open Questions

---

## Key Conventions

### Database
- All primary keys: UUID
- All timestamps: `TIMESTAMPTZ` (timezone-aware)
- Migrations: Alembic only. Never alter the DB schema directly.
- `ledger_entries` and `ledger_transactions` are append-only at both the app layer and the DB layer (PostgreSQL trigger). Do NOT add UPDATE or DELETE logic ever. Corrections are made by posting reversing entries.
- New migrations chain off the current Alembic head using hash-based revision IDs (`alembic revision --autogenerate`). Do NOT hand-number migrations `0002+` — that scheme is stale and those files were removed.

### API
- All routes return typed Pydantic response models — no raw dicts
- Auth: Bearer JWT in Authorization header
- Idempotency: any endpoint that creates a financial record must accept `Idempotency-Key` header
- Errors: always `{"detail": "<message>"}` — never expose internal exceptions

### Async
- All DB operations use `AsyncSession`. Never use sync `Session` in V2 code.
- All service functions are `async def`
- Background jobs go through ARQ — never `BackgroundTasks` for financial operations

### Testing
- Every new module must have a pytest file under `tests/<module>/`
- Tests use fixtures — never hit a real DB or Brankas API in tests
- Acceptance criteria from the spec map 1:1 to test function names

### Git
- Branch naming: `feature/<module>/<short-description>` (e.g. `feature/banking/brankas-disbursement`)
- PR must include: link to spec, passing tests, updated migration if schema changed
- Specs are reviewed and merged before implementation PRs are opened

---

## Architecture Quick Reference

### Omnibus Money Flow
```
Lender          → [Brankas inbound]  → FL Omnibus Account  → ledger: FUNDING
Borrower        → [Brankas inbound]  → FL Omnibus Account  → ledger: REPAYMENT
FL Omnibus Acct → [Brankas outbound] → Borrower            → ledger: DISBURSEMENT
FL Omnibus Acct → [Brankas outbound] → Lender              → ledger: DISTRIBUTION
FL Omnibus Acct → [internal]         → FL Revenue           → ledger: FEE
```

### Core Lending State Machine
```
LoanApplication:  DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED | REJECTED
ScoreRun:         RUNNING → READY → LOCKED
Contract:         DRAFT → SIGNED → ACTIVE_PENDING_FUNDING → ACTIVE_FUNDED → CLOSED
Listing:          DRAFT → OPEN → FUNDED → CLOSED
Order:            PENDING_PAYMENT → FILLED | CANCELLED | EXPIRED
```

### User Roles
- `SME` — borrower. Creates projects, submits loan applications.
- `INVESTOR` — lender. Places orders on listings, receives distributions.
- `ADMIN` — FL operations staff. Approves score runs, triggers disbursements.

---

## ADR Index

| ID | Title | Status |
|---|---|---|
| ADR-001 | Modify MVP codebase, do not rebuild | Accepted |
| ADR-002 | Omnibus/custodial account via Brankas | Accepted |
| ADR-003 | Omnibus-first with escrow-compatible ledger seam | Accepted |
| ADR-004 | Vietnam regulatory compliance (Decree 94 + Circular 64) | Draft |
| ADR-005 | Permanent local dev environment + local knowledge MCP server | Accepted |
| ADR-006 | fl-knowledge: BM25 → Pinecone + local embeddings | Accepted |

Full ADRs in `docs/adr/`.

---

## What Edward Does NOT Do

Edward is CTO and backend/architecture owner. **Edward does not write UI code.** If a task involves React, CSS, component design, or anything rendered in a browser, it belongs to Phat. Do not suggest or generate frontend code in Edward's sessions.

---

## Local Dev Environment & Knowledge MCP

**Standing local stack (ADR-005):** run the repo's `docker-compose.yml` services — `postgres`, `mailpit`, `minio` — as a long-lived environment (`docker compose up -d`); app code runs on the host via `.venv` + `uvicorn` for hot reload. The dev database is standardized on the compose Postgres: `postgresql+psycopg2://fundlok:fundlok@localhost:5433/fundlok_dev`. Run `docker compose up -d postgres` before `alembic upgrade head` or starting the app.

**fl-knowledge MCP server (ADR-005 → ADR-006):** a project-scoped MCP server at `tools/mcp-servers/fl-knowledge/`, registered via `.mcp.json`, that indexes `CLAUDE.md`, `AGENTS.md`, `README.md`, and everything under `docs/`, exposing `search_fl_docs` and `reindex_fl_docs`. It began on BM25 lexical search (ADR-005) and moved to local `sentence-transformers` embeddings + Pinecone (ADR-006). **Prefer `search_fl_docs` over re-reading whole specs/ADRs** — it's the token-efficient way to pull context. Requires a one-time `build_index.py` run and a `PINECONE_API_KEY` in a gitignored local `.env`; the server points you at `build_index.py` if the index is missing. `docs/` stays the source of truth — the server only reads it.

---

## Current Phase

**Phase 0 — Foundation (complete)**
- [x] Behavioral test suite + CI test job (HANDOFF-01)
- [x] Async DB migration — asyncpg + AsyncSession (HANDOFF-02 Fix A)
- [x] DB-backed refresh token revocation — uses `refresh_tokens` table already in `0001` (HANDOFF-02 Fix B)
- [x] Module cleanup — `app/files/` merged into `app/uploads/` (HANDOFF-02 Fix C)
- [ ] ARQ worker scaffold (deferred)

**Phase 1 — Ledger & Banking (in progress)**
- [x] Internal ledger foundation — double-entry ledger, custodial/ledger accounts, immutability trigger (spec ACCEPTED `docs/specs/ledger/ledger-foundation.md`, ADR-003; implemented in `app/ledger/` + migration `862160bce972`, merged PR #18)
- [ ] Banking Open API integration (Circular 64) + `bank_transactions` + reconciliation
- [ ] Compliance module — Decree 94 exposure caps, CIC data, reporting (ADR-004)
