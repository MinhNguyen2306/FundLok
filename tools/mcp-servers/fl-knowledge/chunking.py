"""
Shared markdown chunking logic for fl-knowledge, used by both the one-time
indexer (build_index.py) and the MCP server (server.py) so they can never
disagree about what a "chunk" is.
"""

from dataclasses import dataclass
from pathlib import Path

# Repo root is four levels up from this file: tools/mcp-servers/fl-knowledge/chunking.py
REPO_ROOT = Path(__file__).resolve().parents[3]

# Where the knowledge base lives. Add paths here as new doc locations appear.
INDEXED_PATHS = [
    REPO_ROOT / "CLAUDE.md",
    REPO_ROOT / "AGENTS.md",
    REPO_ROOT / "README.md",
    REPO_ROOT / "docs",
]


@dataclass
class Chunk:
    source: str      # file path relative to repo root
    heading: str      # nearest markdown heading, or "(top of file)"
    text: str         # chunk body


def chunk_markdown(path: Path) -> list[Chunk]:
    """Split a markdown file into chunks on '#'-prefixed headings (any level).
    Falls back to treating the whole file as one chunk if it has no headings."""
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    rel = str(path.relative_to(REPO_ROOT))
    lines = raw.splitlines()

    chunks: list[Chunk] = []
    current_heading = "(top of file)"
    current_lines: list[str] = []

    def flush():
        body = "\n".join(current_lines).strip()
        if body:
            chunks.append(Chunk(source=rel, heading=current_heading, text=body))

    for line in lines:
        if line.startswith("#"):
            flush()
            current_heading = line.lstrip("#").strip() or current_heading
            current_lines = [line]
        else:
            current_lines.append(line)
    flush()

    return chunks or [Chunk(source=rel, heading="(whole file)", text=raw)]


def build_corpus() -> list[Chunk]:
    files: list[Path] = []
    for p in INDEXED_PATHS:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.is_file():
            files.append(p)

    corpus: list[Chunk] = []
    for f in files:
        corpus.extend(chunk_markdown(f))
    return corpus


def chunk_id(chunk: Chunk, index: int) -> str:
    """Deterministic Pinecone vector ID: stable across re-indexing runs as
    long as file paths and chunk order don't change, so re-running
    build_index.py updates existing vectors in place instead of duplicating."""
    safe_source = chunk.source.replace("/", "__")
    return f"{safe_source}::{index}"
