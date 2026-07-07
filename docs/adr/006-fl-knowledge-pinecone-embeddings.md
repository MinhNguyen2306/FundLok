# ADR-006: fl-knowledge Moves from BM25 to Pinecone + Local Embeddings

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | July 2026 |
| **Deciders** | Edward Wong (CTO) |

## Context

ADR-005 introduced `fl-knowledge`, a local MCP server indexing FundLok's
markdown knowledge base, deliberately using BM25 (lexical/keyword) search
instead of embeddings — reasoning being zero infra, zero cost, and "good
enough" quality for short, precisely worded specs/ADRs. That ADR explicitly
left the door open to revisit this if retrieval quality became a problem or
for learning purposes.

BM25's real limitation: it only matches literal shared words. A query like
"how do lenders get paid back" will not find a section that only says
"pro-rata distributions" — semantically identical, zero token overlap. This
gets worse as `docs/` grows and phrasing across specs/ADRs/handoffs
naturally drifts.

Separately, there's a standing interest in using this project to learn a
production-standard RAG pattern (embeddings + a managed vector database)
rather than staying on a toy keyword index indefinitely.

## Decision

Replace BM25 in `fl-knowledge` with:

- **Local embeddings** via `sentence-transformers` (`all-MiniLM-L6-v2`,
  384-dim). Runs on-device, no API key needed for this step, no per-query
  cost. Chosen over a hosted embedding API (e.g. Voyage, OpenAI) to keep the
  server's total operating cost at zero, since query latency is not a
  concern for this use case.
- **Pinecone** (free/serverless tier) as the vector store. Chosen because
  it's the most widely used managed vector DB, so the workflow learned here
  (upsert vectors + metadata, similarity query, index management) transfers
  directly to other tools and future production RAG work.

Chunking logic is unchanged and now lives in a shared `chunking.py`, used by
both the new one-time indexer (`build_index.py`, embeds + upserts to
Pinecone) and `server.py` (queries Pinecone at request time; never writes to
it). The MCP tool surface (`search_fl_docs`, `reindex_fl_docs`) is unchanged
from ADR-005 — only the implementation behind it changed, so no consumer of
those tools needs to know this happened.

## Consequences

- `fl-knowledge` now depends on an external service (Pinecone) being
  reachable and the index being populated — `build_index.py` must be run
  once before first use, and again after material doc changes. The server
  fails with a clear message pointing at `build_index.py` if the index is
  missing, rather than failing silently.
- A Pinecone API key is required (`PINECONE_API_KEY`, via a local `.env` in
  `tools/mcp-servers/fl-knowledge/`, gitignored — never committed).
- The embedding model download (~90MB, one-time) and Pinecone network calls
  mean this server is no longer purely offline, unlike the ADR-005 version.
  Acceptable tradeoff since query latency was explicitly deprioritized for
  this decision.
- If Pinecone's free tier limits ever become a constraint, or the corpus
  outgrows a single small index, revisit — the swap should again be
  contained to `build_index.py`/`server.py` internals.

## Open Questions

- None currently. Revisit embedding model choice if search quality on
  longer or more technical chunks (e.g. full spec files) turns out weaker
  than on the short ADR-style text this was tuned against.
