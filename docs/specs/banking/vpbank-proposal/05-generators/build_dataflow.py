#!/usr/bin/env python3
"""Section 1.5 data-flow diagram: three zones, labelled flows, explicit non-crossing set."""
import pathlib
OUTDIR = pathlib.Path(__file__).resolve().parent.parent / "04-diagrams"
import html, textwrap

# (ref, label, direction) direction: 'r' = left zone -> right zone, 'l' = right -> left
GAP1 = [
    ("P1", "Identity & enterprise data", "r"),
    ("P2", "Financial statements & appraisal inputs", "r"),
    ("P3", "Settlement account details & consent record", "r"),
    ("P4", "Loan terms, schedule, statements & holdings", "l"),
]
GAP2 = [
    ("F1", "Account provisioning request & permitted-destination list", "r"),
    ("F2", "Payment instructions — dual authorised", "r"),
    ("F3", "Channel administration — authorised users", "r"),
    ("B1", "Escrow account number & status", "l"),
    ("B2", "Instruction acknowledgement & per-transfer outcome", "l"),
    ("B3", "Daily statement & balance", "l"),
]
BYPASS = ("V0", "Account-opening documents for the bank's own due diligence — submitted directly, never routed through FundLok")

NEVER = [
    "Credit score, grade, rate tier or any appraisal output",
    "SME financial statements or supporting documentation",
    "Personal guarantee terms or enforcement detail",
    "Investor portfolio holdings or platform behaviour",
    "Borrower sales data from the T-VAN provider",
    "Any personal data beyond what a named transfer requires",
]

ZONES = [
    ("Parties", "z1", "Investor · SME"),
    ("FundLok", "z2", "arranger & servicer"),
    ("VPBank", "z3", "custodian"),
]

ZW, GAPW = 236, 250
HEAD = 78
ROW = 42
BYP_H = 62
PANEL_H = 132
PAD = 12

box_h = max(len(GAP1), len(GAP2)) * ROW + 30
W = PAD + ZW + GAPW + ZW + GAPW + ZW + PAD
H = HEAD + box_h + BYP_H + PANEL_H + PAD

zx = [PAD, PAD + ZW + GAPW, PAD + 2 * (ZW + GAPW)]
gx = [PAD + ZW, PAD + 2 * ZW + GAPW]

def esc(s):
    return html.escape(s, quote=True)

p = []
a = p.append

# zone boxes
for i, (name, slot, sub) in enumerate(ZONES):
    a(f'<rect class="zone {slot}-zone" x="{zx[i]}" y="{HEAD}" width="{ZW}" height="{box_h}" rx="9"/>')
    a(f'<rect class="zone-top {slot}-fill" x="{zx[i]+10}" y="{HEAD+11}" width="{ZW-20}" height="4" rx="2"/>')
    a(f'<text class="zname" x="{zx[i]+ZW/2}" y="{HEAD+40}" text-anchor="middle">{esc(name)}</text>')
    a(f'<text class="zsub" x="{zx[i]+ZW/2}" y="{HEAD+58}" text-anchor="middle">{esc(sub)}</text>')

# header
a(f'<text class="title" x="{PAD}" y="26">Data and instructions cross the boundary. Money does not.</text>')
a(f'<text class="subtitle" x="{PAD}" y="48">FundLok moves data and instructions, never funds. Every flow below is data or an instruction.</text>')

def draw_flows(flows, x0, x1, ytop):
    for i, (ref, label, d) in enumerate(flows):
        y = ytop + i * ROW + ROW / 2
        pad = 16
        if d == "r":
            x_from, x_to, cls = x0 + 6, x1 - pad, "flow-r"
        else:
            x_from, x_to, cls = x1 - 6, x0 + pad, "flow-l"
        a(f'<line class="{cls}" x1="{x_from}" y1="{y}" x2="{x_to}" y2="{y}" marker-end="url(#ar)"/>')
        lx = (x0 + x1) / 2
        lines = textwrap.wrap(label, 30)
        ly = y - 7 - (len(lines) - 1) * 6
        a(f'<rect class="reftag" x="{lx-88}" y="{ly-13}" width="26" height="14" rx="3"/>')
        a(f'<text class="reftext" x="{lx-75}" y="{ly-2}" text-anchor="middle">{ref}</text>')
        a(f'<text class="flowlabel" x="{lx-56}" y="{ly-2}">')
        for j, ln in enumerate(lines):
            a(f'<tspan x="{lx-56}" dy="{0 if j==0 else 12}">{esc(ln)}</tspan>')
        a('</text>')

draw_flows(GAP1, gx[0], gx[0] + GAPW, HEAD + 22)
draw_flows(GAP2, gx[1], gx[1] + GAPW, HEAD + 22)

# bypass arrow: Parties -> VPBank, routed below FundLok
by = HEAD + box_h + 30
a(f'<path class="bypass" d="M {zx[0]+ZW/2} {HEAD+box_h} V {by} H {zx[2]+ZW/2} V {HEAD+box_h}" marker-end="url(#arMuted)"/>')
ref, label = BYPASS
lines = textwrap.wrap(label, 78)
a(f'<rect class="reftag reftag-muted" x="{W/2-150}" y="{by+7}" width="26" height="14" rx="3"/>')
a(f'<text class="reftext reftext-muted" x="{W/2-137}" y="{by+18}" text-anchor="middle">{ref}</text>')
a(f'<text class="bypasslabel" x="{W/2-118}" y="{by+18}">')
for j, ln in enumerate(lines):
    a(f'<tspan x="{W/2-118}" dy="{0 if j==0 else 12}">{esc(ln)}</tspan>')
a('</text>')

# never-crosses panel
py = HEAD + box_h + BYP_H
a(f'<rect class="panel" x="{PAD}" y="{py}" width="{W-2*PAD}" height="{PANEL_H-14}" rx="9"/>')
a(f'<text class="panel-title" x="{PAD+18}" y="{py+26}">Never crosses to VPBank</text>')
a(f'<text class="panel-sub" x="{PAD+18}" y="{py+43}">VPBank makes no credit decision, so it receives no credit information. Data minimisation is a design rule, not a policy statement.</text>')
for i, item in enumerate(NEVER):
    col, row = i % 2, i // 2
    x = PAD + 18 + col * ((W - 2*PAD - 36) / 2)
    y = py + 66 + row * 17
    a(f'<circle class="bullet" cx="{x+3}" cy="{y-4}" r="2"/>')
    a(f'<text class="panel-item" x="{x+13}" y="{y}">{esc(item)}</text>')

svg_body = "\n".join(p)

rows_html = "\n".join(
    f'<tr><td class="tref">{r}</td><td>{esc(l)}</td><td>{d}</td></tr>'
    for r, l, d in ([(r, l, "Parties → FundLok" if d == "r" else "FundLok → Parties") for r, l, d in GAP1]
                    + [(r, l, "FundLok → VPBank" if d == "r" else "VPBank → FundLok") for r, l, d in GAP2]
                    + [(BYPASS[0], BYPASS[1], "Parties → VPBank, direct")])
)

HTML = f"""<!DOCTYPE html>
<html lang="en" data-palette="#2a78d6,#1baf7a,#4a3aa7">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Section 1.5 — Data flow</title>
<style>
  :root {{
    color-scheme: light;
    --surface-1:#fcfcfb; --plane:#f9f9f7; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10);
    --zonebg:#f6f6f3; --panelbg:#f6f6f3;
    --z1:#2a78d6; --z2:#1baf7a; --z3:#4a3aa7;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
      --zonebg:#201f1e; --panelbg:#201f1e;
      --z1:#3987e5; --z2:#199e70; --z3:#9085e9;
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
    --zonebg:#201f1e; --panelbg:#201f1e;
    --z1:#3987e5; --z2:#199e70; --z3:#9085e9;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:26px 22px 48px;background:var(--plane);color:var(--ink);
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.55}}
  header,figure,details{{max-width:1180px;margin-left:auto;margin-right:auto}}
  h1{{font-size:21px;margin:0 0 6px;letter-spacing:-0.01em}}
  .sub{{color:var(--ink-2);margin:0 0 4px}} .meta{{color:var(--muted);font-size:12.5px;margin:0}}
  .toolbar{{max-width:1180px;margin:16px auto 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
  button{{font:inherit;font-size:12.5px;padding:6px 13px;border-radius:999px;border:1px solid var(--border);
          background:var(--surface-1);color:var(--ink-2);cursor:pointer}}
  .legend{{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--ink-2);align-items:center}}
  .legend .sw{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
  .legend .ln{{display:inline-block;width:22px;border-top:1.8px solid var(--ink-2);margin-right:6px;vertical-align:3px}}
  .legend .ln-d{{border-top-style:dashed;border-color:var(--muted)}}
  .scroller{{overflow-x:auto;background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:6px}}
  svg{{display:block;width:100%;height:auto}}
  .zone{{fill:var(--zonebg);stroke:var(--border);stroke-width:1}}
  .zname{{font-size:14px;font-weight:660;fill:var(--ink)}}
  .zsub{{font-size:10.5px;fill:var(--muted)}}
  .title{{font-size:13.5px;font-weight:660;fill:var(--ink)}}
  .subtitle{{font-size:11px;fill:var(--ink-2)}}
  .flow-r,.flow-l{{stroke:var(--z2);stroke-width:1.7}}
  .bypass{{stroke:var(--muted);stroke-width:1.5;stroke-dasharray:5 4;fill:none}}
  .flowlabel{{font-size:10.5px;fill:var(--ink-2)}}
  .bypasslabel{{font-size:10.5px;fill:var(--muted)}}
  .reftag{{fill:var(--z2)}} .reftag-muted{{fill:var(--muted)}}
  .reftext{{font-size:9.5px;font-weight:700;fill:#fff}}
  .panel{{fill:var(--panelbg);stroke:var(--border);stroke-width:1}}
  .panel-title{{font-size:12.5px;font-weight:660;fill:var(--ink)}}
  .panel-sub{{font-size:10.5px;fill:var(--ink-2)}}
  .panel-item{{font-size:10.5px;fill:var(--ink-2)}}
  .bullet{{fill:var(--muted)}}
  .z1-fill{{fill:var(--z1)}} .z2-fill{{fill:var(--z2)}} .z3-fill{{fill:var(--z3)}}
  figcaption{{font-size:12.5px;color:var(--muted);margin-top:11px}}
  summary{{cursor:pointer;font-size:13px;color:var(--ink-2)}}
  details{{margin-top:24px}}
  table{{border-collapse:collapse;width:100%;margin-top:12px;font-size:12.5px}}
  th,td{{text-align:left;padding:6px 9px;border-bottom:1px solid var(--grid);vertical-align:top}}
  th{{color:var(--muted);font-weight:620;font-size:11px;text-transform:uppercase;letter-spacing:0.04em}}
  .tref{{font-weight:700;color:var(--ink-2);font-variant-numeric:tabular-nums}}
  @media print{{
    body{{padding:0;background:#fff}} .toolbar{{display:none}} details{{display:none}}
    .scroller{{overflow:visible;border:none;padding:0}}
    header{{margin-bottom:8px}} h1{{font-size:14pt}} .sub{{font-size:9.5pt}} .meta{{font-size:8.5pt}}
    figure{{max-width:none;text-align:center}}
    svg{{width:auto!important;height:150mm!important;margin:0 auto}}
    figcaption{{font-size:8pt;text-align:left;margin-top:5px}}
  }}
</style></head>
<body>
<header>
  <h1>Section 1.5 — Data flow</h1>
  <p class="sub">What crosses the boundary between FundLok and VPBank, in which direction, and what deliberately does not.</p>
  <p class="meta">FundLok moves data and instructions, not money. Funds move only between the parties' own accounts and the escrow account held at VPBank.</p>
</header>
<div class="toolbar">
  <button id="themeBtn" type="button">Toggle dark mode</button>
  <div class="legend">
    <span><span class="sw" style="background:var(--z1)"></span>Parties</span>
    <span><span class="sw" style="background:var(--z2)"></span>FundLok</span>
    <span><span class="sw" style="background:var(--z3)"></span>VPBank</span>
    <span><span class="ln"></span>data or instruction</span>
    <span><span class="ln ln-d"></span>direct to the bank, bypassing FundLok</span>
  </div>
</div>
<figure>
  <div class="scroller">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label="Data-flow diagram with three zones: the parties, FundLok, and VPBank. Labelled flows cross each boundary; a dashed flow goes directly from the parties to VPBank bypassing FundLok. A panel lists data that never crosses to VPBank. A full text equivalent follows.">
      <defs>
        <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--z2)"/>
        </marker>
        <marker id="arMuted" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--muted)"/>
        </marker>
      </defs>
{svg_body}
    </svg>
  </div>
  <figcaption>Solid flows are data or instructions. The dashed flow is submitted by the party directly to VPBank and
  never passes through FundLok, because due diligence on account holders is the bank's own.</figcaption>
</figure>
<details open>
  <summary>Text equivalent — every flow</summary>
  <table>
    <thead><tr><th>Ref</th><th>What is exchanged</th><th>Direction</th></tr></thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
</details>
<script>
(function(){{
  document.getElementById('themeBtn').addEventListener('click',function(){{
    var r=document.documentElement;
    var d=r.getAttribute('data-theme')==='dark'||(!r.hasAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);
    r.setAttribute('data-theme',d?'light':'dark');
  }});
}})();
</script>
</body></html>
"""
(OUTDIR / "section-1.5-dataflow.html").write_text(HTML)
print(f"{W}x{H}")
