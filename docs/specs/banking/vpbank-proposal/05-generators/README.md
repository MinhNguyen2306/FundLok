# Generators — VPBank proposal artefacts

Everything in the sibling folders is built from here. The sources of truth are the
markdown section files in `03-section-sources/` (English) and `03-section-sources/vi/`
(Vietnamese). Diagrams have no separate source file: the Python generator *is* the
source, and it emits a self-contained HTML page with the SVG inlined.

## Rebuild everything

```bash
cd 05-generators
./build_all.sh              # diagrams, consolidated documents, PDFs
./build_all.sh --no-pdf     # skip Chromium if Node is not set up
```

## What each script does

| Script | Reads | Writes |
|---|---|---|
| `build_moneyflow.py` | — | `04-diagrams/section-1.4-moneyflow.html` |
| `build_closedloop.py en\|vi` | — | `04-diagrams/section-1.4-closedloop[-VI].html` |
| `build_dataflow.py` | — | `04-diagrams/section-1.5-dataflow.html` |
| `build_swim31.py` | — | `04-diagrams/section-3.1-swimlane.html` |
| `build_consolidated.py` | `03-section-sources/*.md` | `02-english-only/…-EN.md` |
| `build_consolidated_vi.py` | `03-section-sources/vi/*.md` | `01-send-to-team/…-VI.md` |
| `md2html.py IN.md OUT.html` | any of the above | a print-styled intermediate |
| `render_pdfs.mjs [diagrams\|docs]` | the HTML above | PDFs beside each source |

## Requirements

Python needs `markdown` (for `md2html.py` only; the diagram and consolidation
scripts use the standard library alone). PDF rendering needs Node with
`playwright` and a Chromium — set `CHROMIUM=/path/to/chrome` if Playwright cannot
find one itself.

## Conventions worth preserving

**The palette is fixed.** `#2a78d6` principal, `#eb6834` FundLok fee, `#1baf7a`
repayment and allocation, `#4a3aa7` withdrawal and reinvestment. It is validated for
contrast in both light and dark, and the four diagrams are meant to read as one set.
Every generator also emits a dark-mode variant and a full text equivalent of the
diagram as an HTML table, so the artefact stays usable without the picture.

**The consolidation scripts clean as they assemble.** They strip the
`[CONTENT — …]` draft markers and the template's trailing `Dependencies:` line, drop
to-be-confirmed rows whose owner is internal to the engineering team, and renumber
what remains. Each section is preceded by a banner naming where it pastes in
VPBank's own document. Read the `INTERNAL_OWNERS` and `INTERNAL_ITEMS` constants
before adding a new to-be-confirmed row, or it may be filtered out silently — the
script prints what it removed on every run.

**Vietnamese terminology is not free.** `01-send-to-team/VI-GLOSSARY.md` is
mandatory, including its addendum. `build_closedloop.py` holds both languages in one
string table so the two versions cannot drift apart; the older generators predate
that pattern and have Vietnamese only in the section markdown.
