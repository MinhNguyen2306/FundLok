#!/usr/bin/env python3
"""Section 1.4 money-flow diagram: four phases, A4-legible, with legend."""
import pathlib
OUTDIR = pathlib.Path(__file__).resolve().parent.parent / "04-diagrams"
import html, textwrap

BW, BH = 190, 62          # box
XS = [24, 384, 744]       # column x positions; 170px gaps for edge labels
BANDH = 166
HEAD = 84
PAD = 14
W = XS[-1] + BW + 24
NBANDS = 4
H = HEAD + NBANDS*BANDH + 92

def esc(s): return html.escape(s, quote=True)

# kind: pr=principal, fe=fee, rp=repayment, wd=withdrawal/reinvest, es=escrow node
BANDS = [
    ("1", "Funding", "once, as each investor commits", [
        ("Investors × n", "own registered bank accounts", "pr", 0, 0),
        ("Project escrow account", "restricted, at VPBank", "es", 1, 0),
    ], [
        (0, 1, "M1  principal", "pr", 0),
    ]),
    ("2", "Disbursement", "once, when the funding target is met", [
        ("Project escrow account", "restricted, at VPBank", "es", 0, 0),
        ("SME's verified account", "borrower receives 99%", "pr", 2, -30),
        ("FundLok fee account", "disbursement fee, 1%", "fe", 2, 30),
    ], [
        (0, 1, "M2  principal less fee", "pr", -30),
        (0, 2, "M3  disbursement fee", "fe", 30),
    ]),
    ("3", "Daily collection and allocation", "every business day, for the life of the loan", [
        ("SME", "pays % of prior-day revenue", "rp", 0, 0),
        ("Project escrow account", "restricted, at VPBank", "es", 1, 0),
        ("Investor holdings × n", "each investor's own balance", "rp", 2, -30),
        ("FundLok fee account", "loan management fee", "fe", 2, 30),
    ], [
        (0, 1, "M4  daily revenue share", "rp", 0),
        (1, 2, "M5  allocation", "rp", -30),
        (1, 3, "M6  management fee", "fe", 30),
    ]),
    ("4", "Withdrawal or reinvestment", "on the investor's request, through FundLok's platform", [
        ("Investor holding", "available balance", "rp", 0, 0),
        ("Investor's own bank account", "the account they funded from", "wd", 2, -30),
        ("New project escrow", "reinvestment", "wd", 2, 30),
    ], [
        (0, 1, "M7  withdrawal", "wd", -30),
        (0, 2, "M8  reinvestment", "wd", 30),
    ]),
]

p = []
a = p.append

a(f'<text class="title" x="{PAD}" y="26">Money moves only between the parties’ own accounts and the escrow account at VPBank.</text>')
a(f'<text class="subtitle" x="{PAD}" y="46">FundLok issues the instruction for every movement below and holds none of the funds. Its own fee is</text>')
a(f'<text class="subtitle" x="{PAD}" y="61">never an independent movement — it travels inside an instruction that pays a beneficiary in the same breath.</text>')
a(f'<text class="closed" x="{PAD}" y="80">Closed loop: whatever an investor receives can go only to the account that investor funded from.</text>')

for bi, (num, name, freq, nodes, edges) in enumerate(BANDS):
    by = HEAD + bi*BANDH
    a(f'<rect class="{"bandalt" if bi%2 else "band"}" x="0" y="{by}" width="{W-PAD}" height="{BANDH}" rx="8"/>')
    a(f'<circle class="phnum-bg" cx="{PAD+14}" cy="{by+22}" r="11"/>')
    a(f'<text class="phnum" x="{PAD+14}" y="{by+26}" text-anchor="middle">{num}</text>')
    a(f'<text class="phname" x="{PAD+32}" y="{by+26}">{esc(name)}</text>')
    a(f'<text class="phfreq" x="{PAD+32}" y="{by+42}">{esc(freq)}</text>')

    pos = []
    for label, sub, kind, xi, yo in nodes:
        x = XS[xi]; y = by + 58 + yo
        pos.append((x, y))
        cls = "nodebox-es" if kind == "es" else "nodebox"
        a(f'<rect class="{cls} k-{kind}" x="{x}" y="{y}" width="{BW}" height="{BH}" rx="7"/>')
        a(f'<rect class="nodeedge f-{kind}" x="{x}" y="{y}" width="3.5" height="{BH}" rx="1.75"/>')
        ll = textwrap.wrap(label, 24)
        ty = y + (24 if len(ll) == 1 else 19)
        a(f'<text class="nodelabel" x="{x+13}" y="{ty}">')
        for i, ln in enumerate(ll):
            a(f'<tspan x="{x+13}" dy="{0 if i==0 else 13}">{esc(ln)}</tspan>')
        a('</text>')
        sl = textwrap.wrap(sub, 27)
        sy = ty + len(ll)*13 + 3
        a(f'<text class="nodesub" x="{x+13}" y="{sy}">')
        for i, ln in enumerate(sl):
            a(f'<tspan x="{x+13}" dy="{0 if i==0 else 11}">{esc(ln)}</tspan>')
        a('</text>')

    for fi, ti, label, kind, yo in edges:
        x1 = pos[fi][0] + BW; y1 = pos[fi][1] + BH/2
        x2 = pos[ti][0];      y2 = pos[ti][1] + BH/2
        mx = (x1 + x2) / 2
        if abs(y1 - y2) < 2:
            a(f'<line class="edge e-{kind}" x1="{x1+4}" y1="{y1}" x2="{x2-9}" y2="{y2}" marker-end="url(#a-{kind})"/>')
        else:
            a(f'<path class="edge e-{kind}" d="M {x1+4} {y1} H {mx} V {y2} H {x2-9}" marker-end="url(#a-{kind})"/>')
        ly = (y1 - 9) if abs(y1 - y2) < 2 else (y2 - 9)
        plate_w = len(label)*5.4 + 10
        a(f'<rect class="plate {"bandalt" if bi%2 else "band"}" x="{mx-plate_w/2}" y="{ly-10}" '
          f'width="{plate_w}" height="13" rx="3"/>')
        a(f'<text class="edgelabel t-{kind}" x="{mx}" y="{ly}" text-anchor="middle">{esc(label)}</text>')

# footer note
fy = HEAD + NBANDS*BANDH + 22
a(f'<text class="note" x="{PAD}" y="{fy}">M3 and M6 are the only movements to FundLok. Each is a fixed proportion of the instruction it travels in, so VPBank can verify it on</text>')
a(f'<text class="note" x="{PAD}" y="{fy+15}">the face of the instruction. Neither can be issued on its own, and neither can draw on a balance that is sitting idle.</text>')
a(f'<text class="note" x="{PAD}" y="{fy+37}">The disbursement fee (M3) is funded by the SME, whose repayment obligation is calculated on the gross principal — so investors</text>')
a(f'<text class="note" x="{PAD}" y="{fy+52}">remain whole on their full capital. The loan management fee (M6) is funded by the investors, out of return and never principal.</text>')

svg_body = "\n".join(p)

LEG = [("pr","Principal"),("fe","FundLok fee"),("rp","Repayment & allocation"),("wd","Withdrawal & reinvestment")]
legend = "\n".join(
    f'<span><span class="sw sw-{k}"></span>{esc(v)}</span>' for k, v in LEG
)

rows = []
for num, name, freq, nodes, edges in BANDS:
    for fi, ti, label, kind, yo in edges:
        ref, desc = label.split("  ", 1)
        rows.append(f'<tr><td class="tref">{ref}</td><td>{esc(desc)}</td>'
                    f'<td>{esc(nodes[fi][0])}</td><td>{esc(nodes[ti][0])}</td>'
                    f'<td>{esc(freq)}</td></tr>')
table = "\n".join(rows)

HTML = f"""<!DOCTYPE html>
<html lang="en" data-palette="#2a78d6,#eb6834,#1baf7a,#4a3aa7">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Section 1.4 — Money flow</title>
<style>
  :root {{
    color-scheme: light;
    --surface-1:#fcfcfb; --plane:#f9f9f7; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
    --grid:#e1e0d9; --border:rgba(11,11,11,0.10);
    --band:#fcfcfb; --bandalt:#f6f6f3; --cellbg:#ffffff; --esbg:#f1f0ec;
    --pr:#2a78d6; --fe:#eb6834; --rp:#1baf7a; --wd:#4a3aa7;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --border:rgba(255,255,255,0.10);
      --band:#1a1a19; --bandalt:#201f1e; --cellbg:#242422; --esbg:#2b2a27;
      --pr:#3987e5; --fe:#d95926; --rp:#199e70; --wd:#9085e9;
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --border:rgba(255,255,255,0.10);
    --band:#1a1a19; --bandalt:#201f1e; --cellbg:#242422; --esbg:#2b2a27;
    --pr:#3987e5; --fe:#d95926; --rp:#199e70; --wd:#9085e9;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:26px 22px 48px;background:var(--plane);color:var(--ink);
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.55}}
  header,figure,details{{max-width:1160px;margin-left:auto;margin-right:auto}}
  h1{{font-size:21px;margin:0 0 6px;letter-spacing:-0.01em}}
  .sub{{color:var(--ink-2);margin:0 0 4px}} .meta{{color:var(--muted);font-size:12.5px;margin:0}}
  .toolbar{{max-width:1160px;margin:16px auto 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
  button{{font:inherit;font-size:12.5px;padding:6px 13px;border-radius:999px;border:1px solid var(--border);
          background:var(--surface-1);color:var(--ink-2);cursor:pointer}}
  .legend{{margin-left:auto;display:flex;gap:15px;flex-wrap:wrap;font-size:12.5px;color:var(--ink-2);align-items:center}}
  .legend .sw{{display:inline-block;width:20px;height:3px;border-radius:2px;margin-right:6px;vertical-align:3px}}
  .sw-pr{{background:var(--pr)}} .sw-fe{{background:var(--fe)}} .sw-rp{{background:var(--rp)}} .sw-wd{{background:var(--wd)}}
  .scroller{{overflow-x:auto;background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:6px}}
  svg{{display:block;width:100%;height:auto}}
  .band{{fill:var(--band)}} .bandalt{{fill:var(--bandalt)}}
  .nodebox{{fill:var(--cellbg);stroke:var(--border);stroke-width:1}}
  .nodebox-es{{fill:var(--esbg);stroke:var(--border);stroke-width:1.4}}
  .nodelabel{{font-size:11.5px;font-weight:620;fill:var(--ink)}}
  .nodesub{{font-size:10px;fill:var(--muted)}}
  .edge{{fill:none;stroke-width:1.8}}
  .e-pr{{stroke:var(--pr)}} .e-fe{{stroke:var(--fe)}} .e-rp{{stroke:var(--rp)}} .e-wd{{stroke:var(--wd)}}
  .edgelabel{{font-size:10px;font-weight:620}}
  .t-pr{{fill:var(--pr)}} .t-fe{{fill:var(--fe)}} .t-rp{{fill:var(--rp)}} .t-wd{{fill:var(--wd)}}
  .f-pr{{fill:var(--pr)}} .f-fe{{fill:var(--fe)}} .f-rp{{fill:var(--rp)}} .f-wd{{fill:var(--wd)}} .f-es{{fill:var(--muted)}}
  .title{{font-size:13.5px;font-weight:660;fill:var(--ink)}}
  .subtitle{{font-size:11px;fill:var(--ink-2)}}
  .closed{{font-size:11.5px;font-weight:660;fill:var(--rp)}}
  .phnum{{font-size:10.5px;font-weight:700;fill:var(--surface-1)}}
  .phnum-bg{{fill:var(--ink)}}
  .phname{{font-size:12.5px;font-weight:660;fill:var(--ink)}}
  .phfreq{{font-size:10px;fill:var(--muted)}}
  .note{{font-size:10px;fill:var(--ink-2)}}
  .plate{{stroke:none}}
  figcaption{{font-size:12.5px;color:var(--muted);margin-top:11px}}
  summary{{cursor:pointer;font-size:13px;color:var(--ink-2)}} details{{margin-top:24px}}
  table{{border-collapse:collapse;width:100%;margin-top:12px;font-size:12.5px}}
  th,td{{text-align:left;padding:6px 9px;border-bottom:1px solid var(--grid);vertical-align:top}}
  th{{color:var(--muted);font-weight:620;font-size:11px;text-transform:uppercase;letter-spacing:0.04em}}
  .tref{{font-weight:700;color:var(--ink-2)}}
  @media print{{
    body{{padding:0;background:#fff}} .toolbar{{display:none}} details{{display:none}}
    .scroller{{overflow:visible;border:none;padding:0}}
    header{{margin-bottom:6px}} h1{{font-size:13pt}} .sub{{font-size:9pt}} .meta{{font-size:8pt}}
    figure{{max-width:none;text-align:center}}
    svg{{width:auto!important;height:158mm!important;margin:0 auto}}
    figcaption{{font-size:8pt;text-align:left;margin-top:4px}}
  }}
</style></head>
<body>
<header>
  <h1>Section 1.4 — Money flow</h1>
  <p class="sub">Eight movements, four phases, one closed loop. FundLok instructs every movement and holds none of the funds.</p>
  <p class="meta">Working case for illustration: loan of VND 2.5 billion, eight participating investors, 1% disbursement fee.</p>
</header>
<div class="toolbar">
  <button id="themeBtn" type="button">Toggle dark mode</button>
  <div class="legend">{legend}</div>
</div>
<figure>
  <div class="scroller">
    <svg viewBox="0 0 {W} {H}" role="img" aria-label="Money-flow diagram in four phases: funding, disbursement, daily collection and allocation, and withdrawal or reinvestment. Eight movements labelled M1 to M8. A full text equivalent follows.">
      <defs>
        <marker id="a-pr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--pr)"/></marker>
        <marker id="a-fe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--fe)"/></marker>
        <marker id="a-rp" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--rp)"/></marker>
        <marker id="a-wd" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--wd)"/></marker>
      </defs>
{svg_body}
    </svg>
  </div>
  <figcaption>Colour carries the kind of movement, per the legend; the M-references match the inventory in Section 1.4.1.
  The only two movements to FundLok are M3 and M6, and neither can be issued on its own.</figcaption>
</figure>
<details open>
  <summary>Text equivalent — the eight movements</summary>
  <table>
    <thead><tr><th>Ref</th><th>Movement</th><th>From</th><th>To</th><th>When</th></tr></thead>
    <tbody>
{table}
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
(OUTDIR / "section-1.4-moneyflow.html").write_text(HTML)
print(f"{W}x{H}")
