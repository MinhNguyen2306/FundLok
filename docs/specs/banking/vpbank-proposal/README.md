# FundLok × VPBank — partnership proposal response

FundLok's response to VPBank's collaboration proposal, covering the ten sections
assigned to Edward. VPBank is being asked to act as neutral custodian for a restricted
escrow account per loan; FundLok builds, operates and pays for everything else.

**Status:** all ten assigned sections drafted, English and Vietnamese. One blocking
correction outstanding before anything goes to VPBank (see below). Appendices C and E
await a scope decision.

## The structure being proposed

Four parties, four distinct roles, no party holding two of them. The investor is the
lender of record. The SME is the borrower. FundLok is arranger and servicer — it issues
every payment instruction and holds none of the funds. VPBank is custodian and moves
the money. Repayment is a share of the SME's prior-day revenue, read daily from
e-invoice data through a licensed T-VAN provider, rather than a fixed instalment
schedule.

Two properties carry the argument. The loop is closed: whatever an investor receives can
leave only to the bank account that investor originally funded from, recorded when their
money first arrives. And FundLok's fee is never an independent movement — it travels as a
line inside an instruction that pays a beneficiary in the same movement, as a proportion
VPBank can verify on the face of the instruction, subject to a registered ceiling. Both
are set out in section 1.4 and drawn in `04-diagrams/section-1.4-closedloop`.

Section 1.8 offers VPBank two account structures. Option A is a single FBO escrow account
per loan in FundLok's name, with investor entitlement tracked in FundLok's ledger.
Option B gives each investor their own escrow account at VPBank, so daily allocation is a
real bank movement. B is recommended, conditional on two confirmations from VPBank, with
A as the stated fallback.

## Folder layout

`01-send-to-team/` — the Vietnamese consolidated response and the mandatory translation
glossary. This is what goes to the team for pasting into VPBank's document.

`02-english-only/` — the same response in English for internal review, plus two internal
working notes: the partnership issues register (what is open, what it costs, where to
offer help and where not to) and a summary of how money moves and how FundLok is paid.
Neither internal note goes to VPBank.

`03-section-sources/` — the per-section markdown that everything else is assembled from.
English at the top level, Vietnamese under `vi/`. **Edit here, not in the consolidated
files**, then rebuild.

`04-diagrams/` — four self-contained HTML diagrams, each with a dark mode and a text
equivalent. Referenced by number from the sections that use them.

`05-generators/` — the build scripts. See its README.

`_superseded/` — the original fifteen-page lifecycle spec, kept for history. It violates
several of the proposal's universal rules and carries a warning header; do not send it.

## Rules that apply to every section

These come from the document tracker and are not negotiable. No mention of the Decree 94
sandbox. Never imply that VPBank relies on FundLok's AML controls or bears any credit
risk. Never price VPBank's internal cost in VND. Every figure carries its assumption and
source. Unknowns appear as "to be confirmed" with a named owner, never as silence. The
final deliverable is Vietnamese, and tables are fully populated.

## Outstanding

**Blocking.** Section 1.7 still states that funds never leave escrow to a FundLok account,
which contradicts the agreed fee mechanism. It needs a third permitted-destination entry,
narrowly scoped to the agreed fee. Owner: Cường. This should be fixed before VPBank reads
the document rather than discovered by them.

**Also open.** The T-VAN integration is unbuilt and nothing for it appears in the
repository — it is a dependency of the money flow, not a reporting nicety (Phat). The
man-day estimates in 3.6 want validation before external use (Huy). Hosting is outside
Vietnam today, disclosed proactively in 4.4.6 with a pre-launch commitment to migrate
(Edward). Five questions for counsel are listed in 4.4.10. Fee rates and both ceilings are
to be confirmed with VPBank — the ceiling matters more than the rate. And the scope of
appendices C and E needs a call from Loc; C cannot be written without VPBank's cut-off
times and value dating.

**The one question that unblocks the most.** Can VPBank's existing blocked-account product
serve as the restricted escrow account, with a bank-enforced permitted-destination list?
Yes to both makes phase 1 roughly 29.5 man-days of configuration. No makes it 112.5 of
build. Section 3.3.2 states it precisely.
