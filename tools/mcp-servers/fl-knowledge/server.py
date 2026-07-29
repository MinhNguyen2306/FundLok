"""
fl-knowledge: an MCP server that indexes FundLok's own markdown knowledge
base (specs, ADRs, handoffs, CLAUDE.md, AGENTS.md, README) and exposes a
semantic-search tool over it, backed by a Pinecone vector index.

Architecture:
- Embeddings are generated locally with sentence-transformers
  (all-MiniLM-L6-v2, 384-dim) -- no per-query API cost, no network
  dependency for the embedding step itself.
- Vectors + metadata (source file, heading, text) live in a Pinecone
  serverless index. Populate/refresh it with build_index.py in this folder
  -- this server only queries, it never writes to the index.
- This upgrades from an earlier BM25 (keyword) version of this server: BM25
  only matches literal shared words between query and text; embeddings match
  on meaning, so e.g. a query about "how lenders get paid back" can find a
  section that only says "pro-rata distributions" with zero word overlap.

Setup: see README.md in this folder. Requires PINECONE_API_KEY (via .env in
this folder) and a Pinecone index already populated by build_index.py.

This is a stdio MCP server -- it's meant to be launched by an MCP client
(Claude Code, via .mcp.json at the repo root), not run standalone in a
terminal for interactive use.
"""

import asyncio
import os

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "fl-knowledge")


class VectorSearch:
    """Lazy-loaded wrapper around the embedding model + Pinecone index.

    Loaded lazily (not at import time) so that `list_tools` still works even
    if PINECONE_API_KEY is missing or the index doesn't exist yet -- the
    error only surfaces when a search is actually attempted, with a message
    pointing at build_index.py.
    """

    def __init__(self):
        self._model: SentenceTransformer | None = None
        self._index = None

    def _ensure_ready(self):
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL)
        if self._index is None:
            api_key = os.environ.get("PINECONE_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "PINECONE_API_KEY is not set. Copy .env.example to .env "
                    "in tools/mcp-servers/fl-knowledge/ and paste your key in."
                )
            pc = Pinecone(api_key=api_key)
            existing = {i["name"] for i in pc.list_indexes()}
            if INDEX_NAME not in existing:
                raise RuntimeError(
                    f"Pinecone index '{INDEX_NAME}' doesn't exist yet. Run "
                    f"`python3 build_index.py` in this folder first."
                )
            self._index = pc.Index(INDEX_NAME)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        self._ensure_ready()
        vector = self._model.encode(query, normalize_embeddings=True).tolist()
        result = self._index.query(vector=vector, top_k=top_k, include_metadata=True)
        return result.get("matches", [])

    def stats(self) -> dict:
        self._ensure_ready()
        return self._index.describe_index_stats()


search_backend = VectorSearch()
server = Server("fl-knowledge")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_fl_docs",
            description=(
                "Searches the FundLok project knowledge base -- CLAUDE.md, AGENTS.md, "
                "README.md, and everything under docs/ (architecture decisions, ADRs, "
                "spec docs, handoffs, PR writeups, and external source documents like "
                "regulations under docs/regulatory/) -- indexed as embeddings in "
                "Pinecone, ranked by meaning rather than exact keyword match. Use this "
                "before answering any question about existing design decisions, prior "
                "spec iterations, regulatory requirements, or codebase conventions, "
                "since this information may not be in the current conversation context. "
                "Prefer this over re-reading whole files when only one section is needed. "
                "Note: for exhaustive review of a single long document (e.g. a full "
                "gap analysis against a regulation), read that file directly instead -- "
                "this tool returns only the top-k most relevant chunks, not full coverage."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A natural-language question or description of what you're looking for, e.g. 'how do lenders get paid after a borrower repays' or 'brankas webhook retry behavior'.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Max number of matching sections to return (default 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="reindex_fl_docs",
            description=(
                "Re-embed and re-upsert all docs into Pinecone. Run this after "
                "editing specs/ADRs/handoffs so search reflects the latest "
                "content -- equivalent to running build_index.py."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "reindex_fl_docs":
        # Reuse build_index.py's logic rather than duplicating it.
        import build_index
        build_index.main()
        stats = search_backend.stats()
        return [TextContent(type="text", text=f"Reindexed. Index stats: {stats}")]

    if name == "search_fl_docs":
        query = arguments.get("query", "")
        top_k = int(arguments.get("top_k", 5))
        try:
            matches = search_backend.search(query, top_k=top_k)
        except RuntimeError as e:
            return [TextContent(type="text", text=str(e))]

        if not matches:
            return [TextContent(type="text", text="No matching sections found.")]

        blocks = []
        for m in matches:
            meta = m.get("metadata", {})
            source = meta.get("source", "unknown")
            heading = meta.get("heading", "")
            text = meta.get("text", "")
            blocks.append(f"### {source} — {heading}  (score: {m['score']:.3f})\n{text}")
        return [TextContent(type="text", text="\n\n---\n\n".join(blocks))]

    raise ValueError(f"Unknown tool: {name}")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
