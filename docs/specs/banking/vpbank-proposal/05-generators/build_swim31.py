#!/usr/bin/env python3
"""Section 3.1 swimlane: vertical lanes (4 parties) x 9 step rows, A4-portrait legible."""
import pathlib
OUTDIR = pathlib.Path(__file__).resolve().parent.parent / "04-diagrams"
import html, textwrap

PARTIES = [
    ("Investor", "p1", "lender of record"),
    ("SME", "p2", "borrower"),
    ("FundLok", "p3", "arranger & servicer"),
    ("VPBank", "p4", "custodian"),
]

# step no, title, owner, then one cell per party ("" = no action)
STEPS = [
    ("1", "Investor onboarding & account opening", "VPBank — Onboarding (account) · FundLok — Onboarding Ops (platform)", [
        "Registers on platform; submits documents to the bank",
        "",
        "Platform registration; suitability record",
        "Performs its own KYC/CDD; opens investor account (§1.8)",
    ]),
    ("2", "SME onboarding, appraisal & listing", "FundLok — Credit & Underwriting", [
        "Reviews published listings",
        "Registers; submits financials and personal guarantee",
        "Appraisal; assigns rate tier; publishes listing",
        "No appraisal and no credit decision",
    ]),
    ("3", "Escrow account provisioning", "VPBank — Custody Operations", [
        "",
        "",
        "Requests account; supplies permitted-destination list",
        "Opens restricted escrow account; sets destinations + dual control",
    ]),
    ("4", "Loan agreement execution", "FundLok — Platform & Legal Ops", [
        "Signs loan agreement + management authorisation",
        "Signs loan agreement + platform terms",
        "Generates contracts; records commitment",
        "Not a party to the loan agreement",
    ]),
    ("5", "Funding into escrow", "Investor (transfer) · VPBank — Custody Ops (credit)", [
        "Funds from own registered account, or from a held balance",
        "",
        "Records originating account; reconciles credit",
        "Credits escrow account; notifies FundLok",
    ]),
    ("6", "Disbursement to the SME", "FundLok — Treasury Ops (instruction) · VPBank — Custody Ops (execution)", [
        "",
        "Receives principal in its verified account",
        "Verifies conditions; instructs payout and 1% fee together",
        "Checks conditions; disburses to whitelisted SME account",
    ]),
    ("7", "Daily revenue-share collection", "SME (payment) · VPBank — Collections", [
        "",
        "Pays % of prior-day revenue, every business day",
        "Reads T-VAN sales; computes the amount due; requests it; reconciles",
        "Credits escrow account; notifies FundLok",
    ]),
    ("8", "Allocation and return to investors", "FundLok — Treasury Ops (instruction) · VPBank — Custody Ops (execution)", [
        "Balance available daily; withdraws to own account on request",
        "",
        "Computes entitlement and fee in one instruction",
        "Allocates to investors; pays FL fee in the same instruction",
    ]),
    ("9", "Closure & release of the escrow account", "FundLok — Reconciliation & Reporting", [
        "Confirms settlement; receives statement",
        "Obligation discharged",
        "Final reconciliation; closes the loan record",
        "Final statement; zero balance; releases account",
    ]),
]

STEP_W = 250
COL_W = 187
HEAD_H = 74
PAD = 8
ROW_MIN = 74
CHARS = 24
BOX_IX, BOX_IY = 8, 8

def wrap(t, w=CHARS):
    return textwrap.wrap(t, width=w) if t else []

def esc(s):
    return html.escape(s, quote=True)

# compute row heights from the tallest cell
rows = []
for num, title, owner, cells in STEPS:
    lines = max([len(wrap(c)) for c in cells] + [1])
    left = len(wrap(title, 26)) + len(wrap("Owner: " + owner, 30))
    h = max(ROW_MIN, lines * 13 + 2 * BOX_IY + 14, left * 12 + 22)
    rows.append(h)

W = STEP_W + len(PARTIES) * COL_W + PAD
H = HEAD_H + sum(rows) + PAD

p = []
a = p.append

# party column bands
for ci, (name, slot, role) in enumerate(PARTIES):
    x = STEP_W + ci * COL_W
    band = "band-alt" if ci % 2 else "band"
    a(f'<rect class="{band}" x="{x}" y="{HEAD_H}" width="{COL_W}" height="{sum(rows)}"/>')

# header
a(f'<rect class="headband" x="0" y="0" width="{W - PAD}" height="{HEAD_H}"/>')
a('<text class="corner" x="12" y="28">Nine-step end-to-end process</text>')
a('<text class="corner-sub" x="12" y="46">onboarding → loan closure</text>')
a('<text class="corner-sub" x="12" y="62">owner named for every step</text>')
for ci, (name, slot, role) in enumerate(PARTIES):
    x = STEP_W + ci * COL_W
    a(f'<rect class="colhead {slot}-fill" x="{x + 6}" y="16" width="{COL_W - 12}" height="4" rx="2"/>')
    a(f'<text class="colname" x="{x + COL_W/2}" y="40" text-anchor="middle">{esc(name)}</text>')
    a(f'<text class="colrole" x="{x + COL_W/2}" y="56" text-anchor="middle">{esc(role)}</text>')

# rows
y = HEAD_H
for ri, ((num, title, owner, cells), rh) in enumerate(zip(STEPS, rows)):
    a(f'<line class="rowsep" x1="0" y1="{y}" x2="{W - PAD}" y2="{y}"/>')
    # step label block
    a(f'<circle class="stepnum-bg" cx="24" cy="{y + 20}" r="11"/>')
    a(f'<text class="stepnum" x="24" y="{y + 24}" text-anchor="middle">{num}</text>')
    tl = wrap(title, 26)
    ty = y + 17
    a(f'<text class="steptitle" x="42" y="{ty}">')
    for i, ln in enumerate(tl):
        a(f'<tspan x="42" dy="{0 if i==0 else 13}">{esc(ln)}</tspan>')
    a('</text>')
    ol = wrap("Owner: " + owner, 30)
    oy = ty + len(tl) * 13 + 6
    a(f'<text class="stepowner" x="42" y="{oy}">')
    for i, ln in enumerate(ol):
        a(f'<tspan x="42" dy="{0 if i==0 else 11}">{esc(ln)}</tspan>')
    a('</text>')
    # party cells
    for ci, ((name, slot, role), text) in enumerate(zip(PARTIES, cells)):
        if not text:
            continue
        x = STEP_W + ci * COL_W
        bx, by = x + BOX_IX, y + BOX_IY
        bw, bh = COL_W - 2 * BOX_IX, rh - 2 * BOX_IY
        neg = text.startswith("No ") or text.startswith("Not ")
        cls = "cell-neg" if neg else "cell"
        a(f'<rect class="{cls} {slot}-cell" x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="5"/>')
        a(f'<rect class="cell-edge {slot}-fill" x="{bx}" y="{by}" width="3" height="{bh}" rx="1.5"/>')
        lines = wrap(text)
        tx = bx + 10
        tyy = by + 15
        tcls = "celltext-neg" if neg else "celltext"
        a(f'<text class="{tcls}" x="{tx}" y="{tyy}">')
        for i, ln in enumerate(lines):
            a(f'<tspan x="{tx}" dy="{0 if i==0 else 13}">{esc(ln)}</tspan>')
        a('</text>')
    y += rh
a(f'<line class="rowsep" x1="0" y1="{y}" x2="{W - PAD}" y2="{y}"/>')
for ci in range(len(PARTIES) + 1):
    x = STEP_W + ci * COL_W
    a(f'<line class="colsep" x1="{x}" y1="0" x2="{x}" y2="{y}"/>')

svg_body = "\n".join(p)

table_rows = "\n".join(
    f'<tr><td class="tnum">{num}</td><td><strong>{esc(title)}</strong><br><span class="tow">{esc(owner)}</span></td>'
    + "".join(f'<td>{esc(c) if c else "—"}</td>' for c in cells) + "</tr>"
    for num, title, owner, cells in STEPS
)

HTML = f"""<!DOCTYPE html>
<html lang="en" data-palette="#2a78d6,#eb6834,#1baf7a,#4a3aa7">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Section 3.1 — Nine-step end-to-end process</title>
<style>
  :root {{
    color-scheme: light;
    --surface-1:#fcfcfb; --plane:#f9f9f7; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10);
    --band:#fcfcfb; --band-alt:#f6f6f3; --cellbg:#ffffff; --headband:#f6f6f3;
    --p1:#2a78d6; --p2:#eb6834; --p3:#1baf7a; --p4:#4a3aa7;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
      --band:#1a1a19; --band-alt:#201f1e; --cellbg:#242422; --headband:#201f1e;
      --p1:#3987e5; --p2:#d95926; --p3:#199e70; --p4:#9085e9;
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#383835; --border:rgba(255,255,255,0.10);
    --band:#1a1a19; --band-alt:#201f1e; --cellbg:#242422; --headband:#201f1e;
    --p1:#3987e5; --p2:#d95926; --p3:#199e70; --p4:#9085e9;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:26px 22px 48px;background:var(--plane);color:var(--ink);
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.55}}
  header,figure,section{{max-width:1060px;margin-left:auto;margin-right:auto}}
  h1{{font-size:22px;margin:0 0 6px;letter-spacing:-0.01em}}
  .sub{{color:var(--ink-2);margin:0 0 4px}}
  .meta{{color:var(--muted);font-size:12.5px;margin:0}}
  .toolbar{{max-width:1060px;margin:16px auto 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
  button{{font:inherit;font-size:12.5px;padding:6px 13px;border-radius:999px;border:1px solid var(--border);
          background:var(--surface-1);color:var(--ink-2);cursor:pointer}}
  .legend{{margin-left:auto;display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--ink-2)}}
  .legend .sw{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:6px;vertical-align:-1px}}
  .scroller{{overflow-x:auto;background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:6px}}
  svg{{display:block;width:100%;height:auto}}
  .band{{fill:var(--band)}} .band-alt{{fill:var(--band-alt)}} .headband{{fill:var(--headband)}}
  .rowsep,.colsep{{stroke:var(--grid);stroke-width:1}}
  .cell{{fill:var(--cellbg);stroke:var(--border);stroke-width:1}}
  .cell-neg{{fill:none;stroke:var(--grid);stroke-width:1;stroke-dasharray:3 3}}
  .celltext{{font-size:10.5px;fill:var(--ink-2)}}
  .celltext-neg{{font-size:10.5px;fill:var(--muted);font-style:italic}}
  .steptitle{{font-size:11.5px;font-weight:640;fill:var(--ink)}}
  .stepowner{{font-size:9.5px;fill:var(--muted)}}
  .stepnum{{font-size:10.5px;font-weight:700;fill:var(--surface-1)}}
  .stepnum-bg{{fill:var(--ink)}}
  .colname{{font-size:13px;font-weight:660;fill:var(--ink)}}
  .colrole{{font-size:10px;fill:var(--muted)}}
  .corner{{font-size:12.5px;font-weight:660;fill:var(--ink)}}
  .corner-sub{{font-size:10px;fill:var(--muted)}}
  .p1-fill{{fill:var(--p1)}} .p2-fill{{fill:var(--p2)}} .p3-fill{{fill:var(--p3)}} .p4-fill{{fill:var(--p4)}}
  figcaption{{font-size:12.5px;color:var(--muted);margin-top:11px}}
  details{{max-width:1060px;margin:26px auto 0}}
  summary{{cursor:pointer;font-size:13px;color:var(--ink-2)}}
  table{{border-collapse:collapse;width:100%;margin-top:12px;font-size:12px}}
  th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--grid);vertical-align:top}}
  th{{color:var(--muted);font-weight:620;font-size:11px;text-transform:uppercase;letter-spacing:0.04em}}
  .tnum{{font-variant-numeric:tabular-nums;color:var(--muted)}}
  .tow{{color:var(--muted);font-size:11px}}
  @media print{{
    body{{padding:0;background:#fff}} .toolbar{{display:none}}
    .scroller{{overflow:visible;border:none;padding:0}} details{{display:none}}
    header{{margin-bottom:8px}} h1{{font-size:14pt}}
    .sub{{font-size:9.5pt;margin-bottom:2px}} .meta{{font-size:8.5pt}}
    figure{{text-align:center}}
    svg{{width:auto!important;height:149mm!important;margin:0 auto}}
    figcaption{{font-size:8pt;text-align:left;margin-top:5px}}
  }}
</style></head>
<body>
<header>
  <h1>Section 3.1 — Nine-step end-to-end process</h1>
  <p class="sub">From party onboarding to loan closure, with the accountable owner named for every step.</p>
  <p class="meta">Four parties, four distinct roles, no party holding two roles. Money moves only through the
  custodian; FundLok moves instructions and data, never funds.</p>
</header>
<div class="toolbar">
  <button id="themeBtn" type="button">Toggle dark mode</button>
  <div class="legend">
    <span><span class="sw" style="background:var(--p1)"></span>Investor — lender of record</span>
    <span><span class="sw" style="background:var(--p2)"></span>SME — borrower</span>
    <span><span class="sw" style="background:var(--p3)"></span>FundLok — arranger &amp; servicer</span>
    <span><span class="sw" style="background:var(--p4)"></span>VPBank — custodian</span>
  </div>
</div>
<figure>
  <div class="scroller">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label="Nine-step process swimlane. Steps run top to bottom as rows; the four parties are columns. A full text equivalent follows in the table.">
{svg_body}
    </svg>
  </div>
  <figcaption>Dashed, italicised cells state what a party deliberately does <em>not</em> do. Steps run top to
  bottom; parties are the columns.</figcaption>
</figure>
<details open>
  <summary>Text equivalent — the nine steps</summary>
  <table>
    <thead><tr><th>#</th><th>Step &amp; owner</th><th>Investor</th><th>SME</th><th>FundLok</th><th>VPBank</th></tr></thead>
    <tbody>
{table_rows}
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
(OUTDIR / "section-3.1-swimlane.html").write_text(HTML)
print(f"{W}x{H}")
