# ADR-007: fl-knowledge Adds PDF Ingestion (Regulatory Source Documents)

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | July 2026 |
| **Deciders** | Edward Wong (CTO) |

## Context

`fl-knowledge` (ADR-005, ADR-006) only indexed FundLok's own authored
markdown (`CLAUDE.md`, `AGENTS.md`, `README.md`, `docs/**/*.md`). It could
not ingest external source documents, such as the actual text of Circular
64/2024/TT-NHNN (the banking Open API technical standard already referenced
in `CLAUDE.md`'s Tech Stack section and ADR-004), which typically arrive as
PDFs, not markdown.

Without this, source-of-truth regulatory text has to be manually
paraphrased into a spec/ADR by hand before it's searchable at all, which
both loses fidelity and is easy to let go stale.

## Decision

Extend `chunking.py` to also index `.pdf` files found under the same
`INDEXED_PATHS` (so `docs/**/*.pdf`, not just `docs/**/*.md`):

- **Extraction:** `pypdf` (pure Python, no external binary dependency like
  poppler) pulls plain text per page. This is text extraction only, not
  OCR — a scanned/image-only PDF with no text layer will yield nothing.
- **Chunking:** unlike markdown (chunked on headings), PDFs are chunked
  per-page, then split into overlapping ~1000-character windows (150-char
  overlap) to fit the embedding model's ~256-token context limit. The
  overlap prevents a sentence that straddles a window boundary from losing
  its surrounding context in both resulting chunks.
- **Convention:** external source documents (regulations, standards, etc.)
  live under `docs/regulatory/`. First artifact: `docs/regulatory/circular-64-open-api.pdf`.

`build_index.py` and `server.py` required no changes — they already
operate on `chunking.build_corpus()`'s output regardless of source format,
which is the payoff of having centralized chunking logic in ADR-005/006.

## Known limitation

The first ingested PDF (`circular-64-open-api.pdf`) is a browser "print to
PDF" of a legal-library website, not a clean government-issued PDF. Its
first page's extracted text is dominated by site navigation/menu text
("Law Library", login prompts, a Q&A link list) rather than the regulation
itself — the substantive legal text starts appearing from the tail of page
1 onward and is clean by page 2. This is a source-quality issue, not a
pipeline bug; `search_fl_docs` will occasionally surface a low-relevance
nav-text chunk from page 1 for loosely related queries. Acceptable for now
given the rest of the document indexes cleanly; a cleaner source PDF (e.g.
directly from the State Bank of Vietnam) would fix this if it becomes a
recurring problem.

## Consequences

- `tools/mcp-servers/fl-knowledge/requirements.txt` gains `pypdf`.
- Anyone adding a new PDF just drops it under `docs/` (ideally
  `docs/regulatory/` for external source documents, to distinguish them
  from FL's own authored specs/ADRs/handoffs) and re-runs `build_index.py`
  — no code changes needed for future PDFs.
- No PDF ever gets modified or annotated in place — `docs/` remains
  read-only from `fl-knowledge`'s perspective, consistent with ADR-005.

## Open Questions

- Whether to add basic nav/boilerplate filtering (e.g. drop very short,
  highly repeated lines) if more webpage-printout-style PDFs get added and
  page-1-style noise becomes a recurring pattern, rather than one-off tail.
