#!/usr/bin/env bash
# Rebuild every VPBank-proposal artefact from its sources.
#
#   ./build_all.sh          rebuild diagrams, consolidated documents and PDFs
#   ./build_all.sh --no-pdf skip the Chromium step (no Node / Playwright needed)
#
# Sources of truth: 03-section-sources/*.md (English) and 03-section-sources/vi/*.md
# (Vietnamese). Everything else in this folder tree is generated and is gitignored
# where it is binary.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$(cd .. && pwd)"

echo "── diagrams ────────────────────────────────────────────"
python3 build_moneyflow.py
python3 build_dataflow.py
python3 build_swim31.py
python3 build_closedloop.py en
python3 build_closedloop.py vi

echo "── consolidated documents ──────────────────────────────"
python3 build_consolidated.py
python3 build_consolidated_vi.py

if [[ "${1:-}" == "--no-pdf" ]]; then
  echo "── PDFs skipped (--no-pdf) ─────────────────────────────"
  exit 0
fi

echo "── print HTML ──────────────────────────────────────────"
# the two internal notes are hand-authored, not generated — skip them if absent
render() {
  if [[ -f "$1" ]]; then python3 md2html.py "$1" "$2"; else echo "absent, skipped: $(basename "$1")"; fi
}
render "$ROOT/02-english-only/FundLok-VPBank-Response-Consolidated-EN.md" cons-en-print.html
render "$ROOT/01-send-to-team/FundLok-VPBank-Response-Consolidated-VI.md" cons-vi-print.html
render "$ROOT/02-english-only/Partnership-Issues-Register.md"             issues-print.html
render "$ROOT/02-english-only/Money-Flow-and-Fees-Summary.md"             money-print.html

echo "── PDFs ────────────────────────────────────────────────"
node render_pdfs.mjs

echo "── done ────────────────────────────────────────────────"
