#!/usr/bin/env python3
"""Render the lifecycle markdown to a print-styled HTML for Chromium print-to-PDF."""
import markdown, re, pathlib

import sys
SRC, OUT = sys.argv[1], sys.argv[2]
src = pathlib.Path(SRC).read_text()

# Strip the leading H1 (it becomes the cover title) and the metadata table.
body_md = src

md = markdown.Markdown(extensions=["tables", "attr_list", "sane_lists", "toc"])
body = md.convert(body_md)

# Give the FBO code block and the ASCII diagram a monospace treatment already handled by <pre>.

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm; }
@page :first { margin-top: 30mm; }
:root {
  --ink: #14140f; --ink-2: #3f3e3a; --muted: #77756e;
  --rule: #ddddd4; --accent: #4a3aa7; --band: #f7f7f4;
}
* { box-sizing: border-box; }
body {
  font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  color: var(--ink); font-size: 9.6pt; line-height: 1.55; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}
h1 { font-size: 19pt; line-height: 1.2; letter-spacing: -0.01em; margin: 0 0 4pt; }
h1 + blockquote { margin-top: 14pt; }
h2 {
  font-size: 12.5pt; margin: 20pt 0 7pt; padding-bottom: 4pt;
  border-bottom: 1.2pt solid var(--accent); break-after: avoid; page-break-after: avoid;
}
h3 { font-size: 10.6pt; margin: 15pt 0 5pt; color: var(--ink);
     break-after: avoid; page-break-after: avoid; }
h2 + p, h3 + p { margin-top: 0; }
p { margin: 0 0 7pt; }
strong { font-weight: 650; }
em { font-style: italic; color: var(--ink-2); }
ul, ol { margin: 0 0 8pt; padding-left: 17pt; }
li { margin-bottom: 3pt; }
code {
  font-family: ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace;
  font-size: 8.4pt; background: var(--band); padding: 0.5pt 3pt; border-radius: 2pt;
}
pre {
  background: var(--band); border: 0.5pt solid var(--rule); border-radius: 4pt;
  padding: 8pt 10pt; overflow: visible; white-space: pre-wrap;
  font-size: 7.6pt; line-height: 1.4; break-inside: avoid; page-break-inside: avoid;
}
pre code { background: none; padding: 0; font-size: inherit; }
blockquote {
  margin: 9pt 0; padding: 7pt 11pt; background: var(--band);
  border-left: 2.5pt solid var(--accent); color: var(--ink-2); font-size: 9pt;
  break-inside: avoid; page-break-inside: avoid;
}
blockquote p:last-child { margin-bottom: 0; }
table {
  border-collapse: collapse; width: 100%; margin: 8pt 0 11pt; font-size: 8.5pt;
  break-inside: auto;
}
th, td { text-align: left; padding: 4.5pt 6pt; border-bottom: 0.5pt solid var(--rule);
         vertical-align: top; }
thead { display: table-header-group; }
th { background: var(--band); font-weight: 650; font-size: 8pt; color: var(--ink); }
tr { break-inside: avoid; page-break-inside: avoid; }
td:first-child { white-space: nowrap; }
td:first-child:has(+ td + td) { white-space: normal; }
hr { border: none; border-top: 0.5pt solid var(--rule); margin: 16pt 0; }
h2, h3 { break-inside: avoid; }
a { color: var(--accent); text-decoration: none; }
"""

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>FundLok x VPBank - Escrow Lifecycle</title>
<style>{CSS}</style></head>
<body>
{body}
</body></html>
"""
pathlib.Path(OUT).write_text(HTML)
print("ok", len(HTML))
