# PR: VPBank escrow partnership — proposal response

**Branch:** `docs/vpbank-partnership-proposal` (off `main` @ `27ba384`)
**Folder README:** [docs/specs/banking/vpbank-proposal/README.md](../specs/banking/vpbank-proposal/README.md)
**Tracker:** CEO-owned document tracker (Google Sheet), rows 2, 3, 5–11 and 14 — Edward's assignments
**Related:** [ADR-003 escrow seam](../adr/) · [Circular 64/2024/TT-NHNN](../regulatory/circular-64-open-api.pdf)

## What this does

Documents-only. Adds FundLok's response to VPBank's collaboration proposal, covering the
ten sections assigned to Edward: 1.4 money flow, 1.5 data flow, 1.8 account structure,
3.1 end-to-end process, 3.3 and 3.4 what VPBank builds in phase 1 and phase 2, 3.5 what
FundLok builds and pays for, 3.6 effort and cost, 3.7 integration and testing, and 4.4
data protection and information security. Nothing under `app/` is touched.

The structure being proposed is four-sided, with each party holding exactly one role: the
investor is lender of record, the SME is borrower, FundLok is arranger and servicer and is
not a party to the loan and does not own the capital, and VPBank is neutral custodian.
Repayment is not an instalment schedule — it is a share of the SME's prior-day revenue,
read each business day from e-invoice data through a licensed T-VAN provider, with the
payment request issued through the platform and Zalo. Eight money movements M1–M8 cover
the whole lifecycle across four phases.

Two properties carry the entire argument and everything else follows from them. **The loop
is closed:** the originating bank account of each investor's inbound payment is recorded at
M1 and becomes the only external destination available to that investor for the life of
the loan, so FundLok cannot direct an investor's money to a third party and an investor
cannot move money to an unverified account. **FundLok's fee is never an independent
movement:** it travels as a line inside an instruction that pays a beneficiary in the same
movement, as a fixed proportion of that instruction, subject to a registered ceiling —
never from an idle balance, never standalone, and suspended while an account is held under
the dispute mechanism. Section 1.4.3 and 1.4.4 state the rules; the two diagrams in 1.4.5
draw them.

Section 1.8 puts two account structures to VPBank explicitly rather than picking one
silently. Option A is a single FBO escrow account per loan in FundLok's name, with investor
entitlement tracked in FundLok's double-entry ledger. Option B gives each investor their
own escrow account at VPBank, so daily allocation is a real bank movement and investor
funds are never inside FundLok's estate. B is recommended, **conditional on two
confirmations from VPBank**, with A as the stated fallback and a named migration trigger
(25 new investor accounts per month) if the pilot starts on A.

Phase 1 is deliberately scoped to need **no API** — 29.5 man-days of configuration if
VPBank's existing blocked-account product can serve as the restricted escrow account with a
bank-enforced permitted-destination list, against 112.5 man-days of build if it cannot.
That single question (3.3.2) moves the timeline from weeks to months and is the first thing
to ask in the meeting. Phase 2 (API, 93–167 man-days) is triggered only at 1,000 payment
events per month sustained over two months. FundLok absorbs its own 64–101 man-days of
build plus roughly 0.5 FTE to operate, stated as a deliberate concession rather than left
to inference.

Sources of truth are `03-section-sources/*.md` for English and `03-section-sources/vi/` for
Vietnamese, the latter written against the mandatory glossary in
`01-send-to-team/VI-GLOSSARY.md` (including its addendum, which fixes terminology that came
back inconsistent from the first translation pass — `movement` → `lượt chuyển tiền`,
`Option A/B` → `Phương án A/B`, and `account frozen` → `bị tạm giữ` rather than `phong toả`,
deliberately, to avoid colliding with VPBank's own blocked-account product name).
`05-generators/` rebuilds every derived artefact from those sources via `build_all.sh`:
four self-contained HTML diagrams, both consolidated documents, and all PDFs.

## Judgment calls worth a second look

**1. Section 1.7 contradicts the agreed fee mechanism, and this PR does not fix it.**
1.7 (not one of Edward's rows) still states that funds never leave the escrow account to a
FundLok account. The confirmed design has FundLok's fee travelling inside beneficiary
instructions, which means the permitted-destination list needs a third entry, narrowly
scoped to the agreed fee and bank-verifiable. Owner: Cường. **This is blocking** — the new
closed-loop diagram draws FundLok's fee account explicitly outside the escrow perimeter
with two arrows reaching it, so the contradiction is now more conspicuous, not less. If
VPBank finds it before we fix it, it costs credibility on the one topic where credibility
matters most.

**2. Option B is recommended but its feasibility is unconfirmed, and its cost is the
largest single exposure in the arrangement.** Under B the daily allocation fans out across
every investor on every active loan: roughly 13,400 movements a month at 60 active loans
against 1,570 under A. At a mid-range per-transaction fee that is about **1.06 billion VND
a year (~USD 42,000)** at month 12, and 1.77 billion at the top of the range. The
mitigating fact, and it is a strong one, is that **interbank volume is identical under both
options** at roughly 1,568 a month — everything B adds settles internally at VPBank, which
costs VPBank very little and exists precisely because the money stays with them rather than
being flushed out daily. The recommendation is therefore to make zero-rated internal
movements a *condition of adopting B*, not something negotiated after the structure is
agreed. Sections 1.8 and the internal issues register both say this; it is a commercial
call for Loc, not an engineering one.

**3. The co-funding offer in 3.6.4 is wider than it should be, and I left it as drafted.**
It currently offers to co-fund four VPBank-side items (A2 the destination list, B5
duplicate-instruction protection, D3/P7 virtual accounts, D5 internal allocation capacity).
That is inconsistent with keeping expenditure low and concedes before being asked. The
issues register recommends narrowing to A2 only and capped, withdrawing B5 entirely (a
duplicated payment is the bank's operational risk at least as much as ours, and banks do
not usually charge a client for their own payment-integrity controls), funding
specification and testing but not build on D3/P7, and reframing D5 as a pricing condition
per point 2 above. **I have not made that edit** — it changes the commercial posture, so it
needs Loc's decision first rather than arriving as a silent diff.

**4. Generated PDFs are gitignored.** `docs/specs/banking/vpbank-proposal/**/*.pdf` plus
the superseded bundle zip. That keeps 4.4 MB of regenerable binaries — which would re-churn
on every document rebuild — out of a 24 MB `.git`. Before committing I rebuilt the whole
tree from a clean directory containing only the markdown sources and the generators, and
confirmed the output is **byte-identical** to what was delivered: same diagram HTML, same
consolidated markdown, same PDF page counts. The cost of the decision is that a reader
without Node and a Chromium cannot produce the print artefacts; `build_all.sh --no-pdf`
covers everyone else, and `render_pdfs.mjs` falls back to a system Chrome if Playwright's
own browser is absent. The existing tracked `docs/regulatory/circular-64-open-api.pdf` is
unaffected by the new pattern (verified with `git check-ignore`).

**5. The consolidation scripts filter to-be-confirmed rows by owner, which can hide a
row.** `build_consolidated.py` drops rows whose owner is internal to the engineering team
(currently `Phat`, plus a named item owned by Huy) so that VPBank does not read our
internal housekeeping as open questions addressed to them. Three rows are removed on the
current run. The filter is by *substring match on the owner cell*, so a new row owned by
Phat or Huy will silently vanish from the outward document — the script prints exactly what
it removed on every run, and `05-generators/README.md` flags it, but it is a footgun worth
knowing about before adding rows.

**6. Hosting is outside Vietnam today.** 4.4.6 discloses this openly, as a pre-launch
commitment to migrate with a stated trigger, rather than omitting it. Being discovered
would be considerably worse than being told. Five further questions are parked for counsel
in 4.4.10: offshore processing of biometric face-match data, whether T-VAN invoice data is
aggregate or invoice-level (and therefore whether it carries the borrower's customers'
personal data), the FBO designation's standing against FundLok's estate under Option A, the
statutory basis for the 10-year retention period, and the lawful-basis analysis overall.

**7. Appendices C and E are not in this PR.** Both are marked "see if needed" on the
tracker. C (SLA, cut-offs, operating calendar) cannot be written without VPBank supplying
cut-off times and value dating, and three sections currently point at it as the home for
that content. E (test and UAT plan) is roughly 80% already inside 3.7. Scope call: Loc.

**8. Man-day estimates are unvalidated.** 3.6's figures are Edward's, not yet reviewed by
Huy. They are internally consistent and every figure carries its assumption and source per
the tracker's universal rules, but they should not go to VPBank as committed numbers before
that review.

## Files

44 files, 11,226 insertions, no binaries.

- `docs/specs/banking/vpbank-proposal/README.md` — folder layout, the structure being
  proposed, the universal rules that bind every section, and everything outstanding.
- `01-send-to-team/` — the Vietnamese consolidated response (60pp) and `VI-GLOSSARY.md`.
  This is what the team pastes into VPBank's own document.
- `02-english-only/` — the English consolidated response (56pp) for internal review, plus
  two internal notes that do **not** go to VPBank: `Partnership-Issues-Register.md` (what
  is open, what it costs, where to offer help and where not to) and
  `Money-Flow-and-Fees-Summary.md`.
- `03-section-sources/` — ten English section sources; `vi/` holds the ten Vietnamese ones.
  Edit here, then rebuild — not in the consolidated files.
- `04-diagrams/` — `section-1.4-moneyflow` (four-phase, eight movements),
  `section-1.4-closedloop` and `-VI` (the closed loop as a swim-lane, with VPBank's
  four-gate control on fee-bearing instructions expanded), `section-1.5-dataflow`
  (three zones plus a "never crosses" panel), `section-3.1-swimlane` (nine steps × four
  parties). Each is a self-contained HTML page with the SVG inlined, a dark mode, and a
  full text equivalent as a table.
- `05-generators/` — eight build scripts, `build_all.sh`, and a README covering the
  pipeline, the fixed palette, and the conventions above.
- `_superseded/vpbank-escrow-lifecycle.md` — the original fifteen-page spec, kept for
  history behind a do-not-send header. It violates several of the tracker's universal
  rules (it mentioned the Decree 94 sandbox fifteen times, implied VPBank relied on our
  AML, and took the fee out of escrow as a standalone movement).
- `.gitignore` — three patterns for the generated artefacts under this folder.

## Verification

- **Reproducibility.** Rebuilt every derived artefact from a clean tree containing only
  the markdown sources and `05-generators/`: diagram HTML and both consolidated markdown
  files come out byte-identical (`cmp`) to the delivered versions, and PDF page counts
  match exactly — EN 56, VI 60, issues register 5, money summary 3, diagrams 1/1/1/2/2.
- **Nothing binary staged.** `git diff --cached --numstat` shows no binary entries across
  all 44 files; the five PDFs and the 2 MB zip remain on disk, correctly ignored.
- **Repository integrity.** `git fsck` clean. Rebased onto `origin/main` @ `27ba384` with
  no conflicts.
- **Cross-references.** Every internal section reference checked by a semantic pass, not
  just a structural one — this caught three wrong pointers a structural check had passed
  (1.4 → "to be confirmed in 3.1.4" twice, correct target 3.1.5; 3.3 → "item 1 of 3.3.9",
  correct target 3.3.10).
- **Vietnamese consistency.** The first translation pass produced six different renderings
  of "movement"; the glossary addendum was extended and 61 instances normalised
  programmatically. The numerals are deliberately left in English format per glossary rule
  3, for a native reviewer to adjust in a later pass — that review has not happened yet.
- **Arithmetic corrected during drafting, worth knowing because the earlier figures
  circulated internally:** the daily-out operational load is 0.14–0.28 FTE, not the ~1.1
  FTE first stated (a 3% interbank failure rate had been applied to internal book
  transfers; exception rates are now split 3% external / 0.2% internal throughout).
  New investor accounts are roughly 1–10 per month, not 200 (positions had been conflated
  with investors, and family-office ticket sizes are far larger) — this is what flipped
  1.8's recommendation toward Option B. 1.8 had quoted Option A volumes using Option B's
  formula (4,400 against a correct 1,568 at 60 active loans). 1.4.7 had omitted M4, the
  largest external flow, from its external-movement count.
- **Diagram rendering** checked in light and dark, and at A4 print size, for every diagram.
- **Not verified:** the man-day estimates (point 8), the Vietnamese register and number
  formatting by a native speaker, and Option B's operational feasibility at VPBank's end
  (points 1 and 2 above are open questions, not findings).
