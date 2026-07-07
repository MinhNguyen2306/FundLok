# ADR-005: Permanent Local Dev Environment + Local Knowledge MCP Server

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | July 2026 |
| **Deciders** | Edward Wong (CTO) |

## Context

FundLok backend development has moved past one-off sessions into ongoing,
iterative work. Two recurring costs showed up:

1. Each AI coding session re-establishes the dev environment from scratch
   (Postgres, mailpit, minio, venv), wasting time and, when done inside an
   agent sandbox, tokens.
2. Neither Claude nor other AI agents carry context between sessions (see
   "AI context rule" in `CLAUDE.md`). Today that means re-reading full specs,
   ADRs, and handoffs every session to reconstruct context, which is slow and
   token-expensive as `docs/` grows.

An audit of the repo found the pieces for (1) mostly already exist
(`docker-compose.yml` defines postgres/mailpit/minio, `.venv` and
`requirements.txt` are present) — the gap is that they aren't run as a
standing environment, and `.env` currently points at a different Postgres
than the one `docker-compose.yml` defines (see Open Questions).

## Decision

**1. Permanent local dev environment.** Run the existing `docker-compose.yml`
stack (`postgres`, `mailpit`, `minio`) as a long-lived local environment on
Edward's MacBook (`docker compose up -d`), rather than starting/stopping it
per session. Application code continues to run on the host via `.venv` +
`uvicorn` for hot reload, per the existing comment in `docker-compose.yml`.
No new services are introduced by this ADR.

**2. Local knowledge MCP server (`fl-knowledge`).** Add a small, local MCP
server (`tools/mcp-servers/fl-knowledge/`) that indexes `CLAUDE.md`,
`AGENTS.md`, `README.md`, and everything under `docs/` (specs, ADRs,
handoffs, PR writeups), and exposes a `search_fl_docs` tool. It uses BM25
(lexical) search via `rank_bm25` — deliberately not embeddings — so there is
no vector DB to run, no embedding API cost, and no GPU dependency. It is
registered as a project-scoped MCP server via `.mcp.json` at the repo root,
so any Claude Code session opened in this repo can use it automatically.

Retrieval quality can be revisited later (e.g. swap in
sentence-transformers + sqlite-vec) if the docs corpus grows past what
keyword search handles well — the tool surface (`search_fl_docs`,
`reindex_fl_docs`) is designed to stay stable across that change.

**3. RAG scope.** "RAG" here means retrieval over FundLok's own written
knowledge base (specs/ADRs/handoffs), not retrieval over the application
database or third-party documentation. This keeps the server simple and
avoids any question of touching production/financial data from a dev tool.

## Why not embeddings/a vector DB from the start

Specs and ADRs in this repo are short, precisely worded, and already follow
a fixed structure (`docs/specs/_TEMPLATE.md`). Lexical search performs well
on that kind of text, and BM25 has zero infra and zero marginal cost per
query. Embeddings are the natural upgrade path if free-text discovery (e.g.
"what did we decide about X" style queries) becomes common enough that
exact keyword matches stop being reliable.

## Consequences

- New directory: `tools/mcp-servers/fl-knowledge/` (server.py, requirements.txt, README.md).
- New file: `.mcp.json` at repo root (Claude Code project MCP config).
- Contributors who want the knowledge server locally must run its one-time
  `pip install -r requirements.txt` in its own venv (see its README) —
  it is intentionally isolated from the app's `requirements.txt` since it's
  a dev tool, not application code.
- `docs/` remains the source of truth; the MCP server only reads it, never
  writes to it. Editing specs/ADRs still goes through the normal spec-driven
  workflow.

## Resolved: `.env` / `docker-compose.yml` port mismatch

Standardized on the `docker-compose.yml` Postgres (`localhost:5433`, user
`fundlok`) as the single dev database, since it's defined in a file checked
into the repo and reproducible for any contributor, whereas whatever was
running natively on `5432` was machine-local and undocumented. `.env` has
been updated to `postgresql+psycopg2://fundlok:fundlok@localhost:5433/fundlok_dev`.
Anyone picking up this repo must run `docker compose up -d postgres` before
`alembic upgrade head` / starting the app.

## Open Questions

- Whether to extend `fl-knowledge`'s index to `app/` module docstrings once
  the async DB migration (Phase 0) lands and module boundaries stabilize.
