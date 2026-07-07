# fl-knowledge MCP server

An MCP server that indexes FundLok's own markdown knowledge base —
`CLAUDE.md`, `AGENTS.md`, `README.md`, and everything under `docs/` (specs,
ADRs, handoffs, PR writeups) — and exposes a `search_fl_docs` tool so Claude
can pull the one relevant section instead of re-reading whole files into
context every session.

## Architecture

- **Embeddings:** generated locally with `sentence-transformers`
  (`all-MiniLM-L6-v2`, 384 dimensions). No per-query API cost, no network
  call needed for the embedding step itself once the model is downloaded.
- **Vector store:** [Pinecone](https://www.pinecone.io) serverless (free
  tier). Stores each chunk's vector plus its source file, heading, and text
  as metadata, so results are readable without a second lookup.
- **Retrieval is semantic, not keyword-based** — a query like "how do lenders
  get paid back" can match a section that only says "pro-rata distributions",
  with zero literal word overlap. (An earlier version of this server used
  BM25 keyword search; this replaces it. See ADR-003 in `docs/adr/` for why
  and when that tradeoff was made.)

`build_index.py` and `server.py` never disagree about what a "chunk" is —
both import the same logic from `chunking.py`.

## One-time setup

```bash
cd tools/mcp-servers/fl-knowledge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and paste in your Pinecone API key (from https://app.pinecone.io)
```

Then build the index (downloads the ~90MB embedding model on first run,
then embeds and upserts every doc chunk into Pinecone):

```bash
python3 build_index.py
```

Re-run `build_index.py` any time docs/specs/ADRs change materially. It's
idempotent — chunk IDs are deterministic, so re-running updates existing
vectors instead of duplicating them.

## Register with Claude Code

Already wired up via `.mcp.json` at the repo root — Claude Code will offer
to enable it the next time you open a session in this repo. If you need to
re-add it manually:

```bash
claude mcp add fl-knowledge -- tools/mcp-servers/fl-knowledge/.venv/bin/python tools/mcp-servers/fl-knowledge/server.py
```

The server reads `PINECONE_API_KEY` from `.env` in this folder at startup
(via `python-dotenv`) — it does not need the key passed through `.mcp.json`,
so no secret ever needs to live in a file that gets committed.

## Tools exposed

- `search_fl_docs(query, top_k=5)` — semantic search across the indexed docs, returns the top matching sections with file, heading, and similarity score.
- `reindex_fl_docs()` — re-embeds and re-upserts everything into Pinecone (same as running `build_index.py`). Run this in-session after editing a spec/ADR/handoff so search reflects the latest content.

## Extending the index

Add new file/directory paths to `INDEXED_PATHS` in `chunking.py`, then
re-run `build_index.py`. Only `.md` files are indexed today; if you want
`app/` module docstrings in scope later, extend `build_corpus()` there.

## Cost / limits to be aware of

- Embedding is local and free regardless of corpus size.
- Pinecone's free tier has index/storage limits well beyond what a docs
  corpus this size needs, but it is a hosted cloud service — check
  [pinecone.io/pricing](https://www.pinecone.io/pricing/) if the corpus
  grows a lot or you add more indexes.
