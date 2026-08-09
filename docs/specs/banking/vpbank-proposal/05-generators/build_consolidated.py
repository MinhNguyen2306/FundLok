#!/usr/bin/env python3
"""Assemble the ten sections into one paste-ready reply document.

Cleaning applied:
  - drops the [CONTENT — ...] draft marker and the template's trailing Dependencies line
  - removes purely internal to-be-confirmed rows (owners Phat / Huy) and renumbers the rest
  - inserts a visible banner before each section saying where it pastes
"""
import re, pathlib

import pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
SRCDIR = ROOT / "03-section-sources"
OUTDIR = ROOT / "02-english-only"

SECTIONS = [
    ("1.4", "Dòng tiền", "Money flow", "section-1.4-money-flow.md",
     "section-1.4-moneyflow (four-phase money-flow diagram) · section-1.4-closedloop (closed-loop swim-lane with VPBank's fee control)"),
    ("1.5", "Dòng dữ liệu", "Data flow", "section-1.5-data-flow.md",
     "section-1.5-dataflow (three-zone data-flow diagram)"),
    ("1.8", "Cấu trúc tài khoản", "Account structure — Option A and Option B", "section-1.8-account-structure.md", None),
    ("3.1", "Quy trình end-to-end", "End-to-end process", "section-3.1-end-to-end-process.md",
     "section-3.1-swimlane (nine-step swim-lane diagram)"),
    ("3.3", "VPBank cần xây — Giai đoạn 1", "What VPBank needs to build — Phase 1", "section-3.3-vpbank-phase-1.md", None),
    ("3.4", "VPBank cần xây — Giai đoạn 2", "What VPBank needs to build — Phase 2", "section-3.4-vpbank-phase-2.md", None),
    ("3.5", "FundLok xây & chi trả", "What FundLok builds and pays for", "section-3.5-fundlok-builds-and-pays.md", None),
    ("3.6", "Ước lượng khối lượng & chi phí", "Effort and cost estimate", "section-3.6-effort-and-cost.md", None),
    ("3.7", "Tích hợp & kiểm thử", "Integration and testing", "section-3.7-integration-and-testing.md", None),
    ("4.4", "Bảo vệ dữ liệu & an toàn thông tin", "Data protection and information security", "section-4.4-data-protection.md", None),
]

# Rows that are purely internal housekeeping. The co-funding row is kept — VPBank should see that
# the amount is undecided rather than read the offer as open-ended — with the owner narrowed to Loc.
INTERNAL_OWNERS = ("Phat",)
INTERNAL_ITEMS = ("Validation of the FundLok estimates",)
REWRITE_OWNER = {"Loc, with Edward and Huy": "Loc"}
removed = []

def clean(num, text):
    # strip the draft marker line plus the rule that follows it
    text = re.sub(r'^\*\[CONTENT[^\]]*\]\*\s*\n+---\s*\n+', '', text, count=1, flags=re.M)
    # strip the template's trailing Dependencies line
    text = re.sub(r'\n---\s*\n+\*Dependencies:.*?\*\s*$', '\n', text, flags=re.S)
    # filter internal-only to-be-confirmed rows, then renumber
    out, n = [], 0
    in_tbc = False
    for line in text.split("\n"):
        if re.match(r'^## [\d.]+ Items to be confirmed', line):
            in_tbc, n = True, 0
        elif line.startswith("## "):
            in_tbc = False
        if in_tbc:
            m = re.match(r'^\| (\d+) \| (.*)$', line)
            if m:
                body = m.group(2)
                cells = [c.strip() for c in body.split("|")]
                owner = cells[2] if len(cells) > 2 else ""
                if any(o in owner for o in INTERNAL_OWNERS) or any(i in cells[0] for i in INTERNAL_ITEMS):
                    removed.append((num, cells[0][:74], owner))
                    continue
                if owner in REWRITE_OWNER:
                    cells[2] = REWRITE_OWNER[owner]
                    body = " | ".join(cells)
                n += 1
                out.append(f"| {n} | {body}")
                continue
        out.append(line)
    return "\n".join(out).strip()

parts = [f"""# FundLok — phản hồi đề xuất hợp tác VPBank
# FundLok — response to the VPBank collaboration proposal

**Bản tiếng Anh để rà soát nội bộ · English version for internal review**
**Ngày / Date: 5 August 2026 · Phần của Edward Wong / Edward Wong's assignments**

---

## Cách dùng tài liệu này · How to use this document

Tài liệu này chứa nội dung cho **mười mục** của đề xuất VPBank. Mỗi mục bắt đầu bằng một dải phân
cách nêu rõ mục đó dán vào đâu trong tài liệu gốc, thay cho dòng `[CONTENT — …]`.

This document holds the content for **ten sections** of the VPBank proposal. Each section begins with
a banner naming where it pastes in the original document, replacing the `[CONTENT — …]` line.

Ba mục có kèm sơ đồ — bốn sơ đồ tổng cộng — được cung cấp thành tệp riêng và cần chèn vào vị trí đã ghi trong mục đó:
Three sections carry diagrams — four in total — supplied as separate files and inserted at the point marked in the text:

- **1.4** — sơ đồ dòng tiền bốn giai đoạn / four-phase money flow
- **1.4** — sơ đồ phân luồng trách nhiệm vòng kín kèm cơ chế kiểm soát phí / closed-loop swim-lane with the fee control
- **1.5** — sơ đồ dòng dữ liệu ba vùng / three-zone data flow
- **3.1** — sơ đồ swim-lane chín bước / nine-step swim-lane

Các mục còn thiếu (Phụ lục C và E) đang chờ quyết định về phạm vi.
The remaining items (Appendices C and E) await a scope decision.

---
"""]

for num, vn, en, fn, diagram in SECTIONS:
    body = clean(num, (SRCDIR / fn).read_text())
    dia = f"\n> **Sơ đồ kèm theo / Diagram:** `{diagram}`\n" if diagram else ""
    parts.append(f"""
<!-- ══════════════════ PASTE INTO SECTION {num} ══════════════════ -->

> ## ▼ Mục {num} — {vn}
> ## Section {num} — {en}
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục {num}.
> Paste the block below in place of `[CONTENT — …]` at section {num}.{dia}

{body}
""")

doc = "\n".join(parts)
(OUTDIR / "FundLok-VPBank-Response-Consolidated-EN.md").write_text(doc)

print(f"written: {len(doc):,} chars, {doc.count(chr(10)):,} lines")
print(f"sections: {doc.count('PASTE INTO SECTION')}")
print(f"\ninternal to-be-confirmed rows removed ({len(removed)}):")
for num, item, owner in removed:
    print(f"  §{num}  {item}  [{owner}]")
