# Module Completion Audit & Flow Readiness — August 2026

| | |
|---|---|
| **Date** | 11 August 2026 |
| **Author** | Edward Wong (CTO), with Claude Opus 5 |
| **Purpose** | Inventory and prioritisation for UI work while partnership terms are open. **Not** an implementation plan. |
| **Method** | Every `.py` file in `app/` read (23 modules, 101 files, 8,312 LOC); all 7 ADRs, 10 specs, 2 frontend specs, 2 handoffs, 3 PR write-ups, ERD, CI/CD doc; all 14 Alembic migrations; all 26 test modules; plus the VPBank proposal bundle — `Partnership-Issues-Register.pdf`, `Money-Flow-and-Fees-Summary.pdf` and `FundLok-VPBank-Response-Consolidated-EN.pdf` under `docs/specs/banking/vpbank-proposal/02-english-only/` (PDFs, so not greppable from the tree — every VPBank citation below is to those three files by section number). **Status is derived from code, not from docs.** Where docs and code disagree, the code wins and the disagreement is recorded. |
| **Repo state** | `main @ 27ba384`; Alembic head `c9f2a71b83e4` (14 migrations); 24 tables. Note `docs/database/erd.md` still says head `6f3a29bbd701` / 22 tables — it predates the two `gverify` tables. |

---

## Executive summary

**What is ready to demo now.** Two flows are genuinely end-to-end today and neither touches an unsigned
partnership: **investor KYC** and **SME KYB**, both via the GVerify module. They are the most complete
subsystem in the platform — 1,352 LOC, 44 tests named against the specs' acceptance criteria, real vendor
calls, app-enforced terminal states, and regression tests that lock in two live provider quirks. Behind
them, **auth and role selection** are solid (DB-backed refresh rotation with reuse detection, working
`require_roles` enforced across 12 of 17 routers). The **borrower application + document upload wizard** is the third
demo-ready flow: R2 presigning is real and the implementation matches `FRONTEND_UPLOAD_SPEC.md`
field-for-field — but two things must be routed around, below.

**The fastest path to a second flow is not a partnership question — it is a wiring PR.** The grading
engine is finished and verified: I re-ran the 10,000-row golden set independently (270,000 assertions,
0 failures). It is also **not connected to anything**. `app/underwriting/service.py` still returns the MVP
mock — `overall_score = 72.50`, `risk_grade = "B"`, `factor_results = {"mock": True}` — and no module
outside `app/underwriting/grading/` imports `grade()`. So the single highest-leverage piece of
non-partnership work in the codebase is finishing `grading-engine-integration.md` (currently DRAFT and
explicitly marked "not yet an implementable plan") and wiring the engine through. That converts the
product's main differentiator from a mock into a real demo. It needs one decision from Phat — the
response shape — and nothing from any bank.

**What is genuinely stuck until partnerships resolve.** Everything downstream of "lender clicks fund":
funding, disbursement, daily collection, allocation, distribution, withdrawal. Not because the code is
weak — `app/ledger/` is the best-engineered module in the repo — but because the VPBank design that
is currently on the table is a *different money model* from the one implemented. Three specifics:

1. **The repayment mechanism is a daily revenue share, not an instalment schedule.** Per VPBank
   §3.5.2 components 10–11, the amount owed each day derives from the borrower's prior-day sales,
   pulled from a licensed **T-VAN** provider. That makes T-VAN a dependency of the money flow itself,
   not a reporting nicety — and it is a partner FundLok has not started on. The issues register lists
   it as open item #3: *"The T-VAN integration is unbuilt and unconfirmed. Nothing appears in the
   repository."* Confirmed — there is no trace of it.
2. **Option A vs Option B is not just a topology choice, it is a schema change.** ADR-003's escrow
   seam models two topologies, `scope IN ('PLATFORM', 'CONTRACT')`. VPBank Option B puts an escrow
   account **in each investor's own name** — a third topology the CHECK constraint does not permit.
   Option B is FundLok's recommendation and is understood to be VPBank's preference, so this is the
   likely outcome, and it is a migration plus a remap, not a config change.
3. **FundLok's fee is not implemented at all.** The fee mechanics are now settled on the partnership
   side (disbursement fee ~1% of gross principal inside the M2 instruction; management fee inside each
   M5 allocation; never a standalone movement). In code, **no `FEE` leg is ever posted and no
   `FL_REVENUE` account is ever created.** `record_repayment` distributes 100% of gross to lenders.
   The ledger *supports* the required shape — a multi-leg transaction with the fee inside it is exactly
   what `post_transaction` is built for, and a test already exercises it — but the payments module
   posts no fee.

**Two things worth knowing before the VPBank meeting.** First, §3.5.1 of the proposal lists "Credit
appraisal & grading engine — In production" and "Marketplace, order book & loan contracts — In
production". The grading engine is built and tested but not wired to any endpoint; the order book
auto-fills with no payment step. Both claims are defensible about the *code* and overstated about the
*running system*. Second, Money-Flow open item #5 says a pro-rata rounding residual must "allocate
deterministically to the largest holder, so FundLok never benefits from rounding". The implementation
allocates the residual to the **last holding by sorted UUID**. The bound is honoured (FundLok never
benefits — the residual always goes to a lender), but the stated rule differs; it is a one-line change.

**Three defects found that will bite UI work.** None are in `known-gaps.md`:

- `GET /admin/overview` returns **500 whenever any user has a NULL role** — which is the normal
  post-registration state, since role is self-selected afterwards. `UserRow.role: str` is
  non-optional against a nullable column. This breaks every mode of the admin console's only
  data endpoint.
- `POST /projects` **500s (`MissingGreenlet`) when an inline `loan_application` is supplied** — an
  implicit lazy load of `LoanApplication.documents` under `AsyncSession`. The `GET /projects` path
  eager-loads and is safe; the POST path does not.
- `GET /projects/public` **returns `[]` for anything created through the API** — `create_project`
  hardcodes `status="DRAFT"`, `display_projects` filters on `status == "ACTIVE"`, and **no API path
  anywhere writes `Project.status = "ACTIVE"`**. The column's server default *is* `ACTIVE` and
  `scripts/seed_data.sql` inserts ACTIVE rows, so the endpoint looks correct on a seeded dev database
  and is empty in any database populated only through the API. That combination is worse than a plain
  bug — it hides itself.

Also: `GET /projects/{project_id}/applications` is documented in `FRONTEND_UPLOAD_SPEC.md` as the
wizard's boot/resume path and **does not exist**. Only `POST /projects`, `GET /projects`, and
`GET /projects/public` are registered.

---

# Part 1 — Completion matrix

Status vocabulary: **Done** = built, behaviour verified against code, no partner dependency in the way ·
**Partial** = built but incomplete, mocked internally, or defective · **Blocked-on-partnership** = cannot
be completed until terms land.

"Interface stable?" answers one question only: *can Phat build UI against this request/response shape
today without rework risk?*

## 1.1 Foundation

| Module / API | Status | Depends on pending partnership terms? | Interfaces/contracts stable? | User-facing use case(s) |
|---|---|---|---|---|
| `app/auth` — register, login, refresh, logout, verify-email, password reset | **Done** | No | **Mostly.** `UserOut`, `RegisterResponse`, `Token` are typed and test-pinned. But 5 of 8 endpoints have no `response_model` and return raw dicts, so generated clients get `any`. `secure=False` on both cookies will need to change for the HTTPS frontend origin — that is an auth-transport change the FE depends on. | All flows (foundation); KYC/onboarding |
| `app/users` — profile, role selection, avatar | **Done** (function) / **Partial** (contract) | No | **No.** `GET /users/me` is the FE's canonical profile shape and is **untyped** — a hand-built 10-field dict, while the typed `UserOut` on login returns 4 fields. Two shapes for one entity. `avatar_url` is a 900s presign that changes on every call and silently nulls when R2 is down. | KYC/onboarding; borrower + lender profile |
| `app/oauth` — Google / Microsoft login | **Partial** | No | No. Returns tokens in the body *and* cookies but **no user object**, so the FE must make a second call to learn whether role selection is needed. | Onboarding |
| `app/utils` — jwt, rbac, audit, r2, password, email, captcha | **Done** | No (vendor: Turnstile, R2, SMTP) | n/a — internal. `require_roles` is clean and used by 12 routers. | All |
| `app/core` — async session, config | **Done** | No | n/a. Fully async: `create_async_engine` + `async_sessionmaker`; zero legacy sync SQLAlchemy anywhere in `app/`. | All |
| `app/models` — ORM re-export | **Done** | No | n/a | All |
| `app/lending/models.py` — 12 ORM models (of 24 tables) | **Done** | Partly — see `custodial_accounts` scope under 1.4 | n/a (schema). Note **no Python enums**: every state column is bare `Text` with vocabulary only in DB CHECKs, so OpenAPI exposes no unions for any state machine. | All |
| `app/system` — maintenance mode | **Done** | No | **Yes.** Cleanest contract in the repo: two endpoints, typed both ways, deliberate public/private response split. | Platform ops |
| `app/contact` — support form | **Partial** | No | No — no `response_model`, returns a raw dict; no rate limit. | Marketing/support |
| `app/schemas` — legacy | **Dead code** | No | n/a — `project.py` is 0 bytes, `user.py` is 17 lines fully commented out, imported nowhere. Delete candidate. | — |

## 1.2 Identity verification & documents

| Module / API | Status | Depends on pending partnership terms? | Interfaces/contracts stable? | User-facing use case(s) |
|---|---|---|---|---|
| `app/gverify` — eKYC (`POST /gverify/kyc/verify`, `/handoff`, `/handoff/verify`, `GET /status`) | **Done** | **Yes — GVerify/Datatrust, not signed.** Only a demo tenancy (`TPVDEMO`) has been exercised; `GVERIFY_BASE_URL` has no default. What could change: **rate/fee structure** (billing is per-call and *drives control flow* — fail-fast ordering exists to avoid billable calls); **data schema** (already proven unstable — the published v2.5.1 doc is wrong in two confirmed places, code follows verified live samples); **compliance flow** (liveness is unresolved, spec OQ2). | **Yes.** Typed both ways, app-enforced terminal states, 20 tests named against spec §8's 13 criteria. The FL-facing contract is vendor-shaped but stable. **Caveat:** no frontend contract doc exists for `/gverify/*` — six live endpoints including the phone-QR handoff are documented only in the backend spec. | KYC/onboarding (lender) |
| `app/gverify` — eKYB (`POST /gverify/kyb/verify`, `GET /status`) | **Done** | **Yes — same vendor**, plus indirect dependency on **Tổng Cục Thuế** (state tax registry) reached only through Datatrust. Which registry status values mean "active" is unknown (spec OQ1); code guesses `("đang hoạt động", "active")` pending confirmation. | **Yes**, 24 tests against 15 spec criteria. Two spec sections (§6/§7) are stale relative to the code — they say name-mismatch ⇒ REJECTED; the code returns `MANUAL_REVIEW` and the test asserts the code. | KYC/onboarding (borrower business) |
| `app/verification` — Didit hosted KYC/KYB (`/kyc/*`, `/kyb/*`, `/kyc/webhook`) | **Partial** | **Yes — provider selection undecided.** eKYC spec OQ1: *"Which provider wins long-term… **Needs an ADR**"* — no such ADR exists; ADR index stops at 007. Didit remains the default. | Functionally yes, and `FRONTEND_KYC_SPEC.md` matches it exactly — **but the spec describes a flow scheduled for replacement.** The Didit model is redirect + webhook + poll; GVerify is a blocking synchronous verdict. A FE built strictly to `FRONTEND_KYC_SPEC.md` gets rewritten if GVerify wins. | KYC/onboarding |
| — *sub-finding* | — | — | **Zero tests.** The most security-sensitive code in the audited surface — an unauthenticated public webhook whose only defence is hand-rolled 3-variant HMAC canonicalisation — has no test at all. Also still uses a **sync** `httpx.Client`, so it blocks the event loop (documented, deliberately deferred). | — |
| `app/uploads` — `/uploads/*` (loan wizard, R2) | **Done** | No (vendor: R2) | **Yes — the best-matched contract in the repo.** Verified line-by-line against `FRONTEND_UPLOAD_SPEC.md`: all 6 document types, size caps, extension→content-type map, deterministic key format, 15-min TTL, HEAD-verify before `UPLOADED`, idempotent confirm, and byte-identical error strings. **Zero tests**, so nothing guards this against drift. | Borrower application |
| `app/uploads` — `/files/*` (legacy generic docs) | **Blocked / broken** | No | **No — do not build against it.** `upload_url` is fabricated: `f"{settings.MOCK_UPLOAD_BASE_URL}/..."` → `https://mock-storage.fundlok.local/upload`, a non-resolvable host. No R2 call, no presign. This is the **only** path that can create `KYC_ID` / `KYC_ADDRESS` / `KYC_BUSINESS_REG` `Document` rows — i.e. the documents the listing gate requires. | (intended) KYC document submission |

## 1.3 Underwriting & contracts

| Module / API | Status | Depends on pending partnership terms? | Interfaces/contracts stable? | User-facing use case(s) |
|---|---|---|---|---|
| `app/underwriting/grading` — 22-factor deterministic engine, pricing, 8 gates | **Done** (as a library) | **Yes, on data not commercial terms.** (a) **CIC** — scale unconfirmed (0–700 vs 150–750; observed 442–750). Behavioral carries CIC at full weight and is 14.7% of the rate spread, so a scale error mis-prices every loan. Gate 7 (`cic_floor`, permanent reject ≤500) ships **disabled** for this reason. ADR-004 OQ2 leaves the CIC route open — *direct membership vs via the custodial bank* — which couples CIC to the VPBank outcome. (b) **GSO/SBV** reference data — "TO BE CONFIRMED". | n/a as a library (pure functions, verified). **But nothing calls it** — see next row. | Grading/scoring display |
| — *verification* | — | — | I re-ran the golden set independently: **10,000 rows, 270,000 assertions, 0 failures**, `params_version wb-v0-20260728`. SME-0001 → grade 70.98376463, rate 14.32%. The engine is real. 50 tests across 10 files, incl. an AST-level purity check (no `app.*` import, no `async def`, works with `open`/`socket`/`datetime.now` monkeypatched to raise). | — | — |
| `app/underwriting` — `POST /score-runs`, `POST /score-runs/{id}/approve` | **Partial (mock)** | Indirect | **No.** Still the MVP stub: `overall_score = Decimal("72.50")`, `risk_grade = "B"`, `factor_results = {"mock": True}`, `recommended_terms = {"mode": "default", "rate": "12%"}`. Verified: `app/underwriting/service.py` imports only `LoanApplication, ScoreRun`; **no module in `app/` imports `grade()`**. The integration spec states the response models *"gain the real grade, the four premiums, the price, the repayment schedule, the fired gates and the decision. **Exact shape to be agreed with Phat before implementation.**"* Also: `overall_score` is `Numeric(5,2)` and lossy; `ScoreRun.status` must grow `INSUFFICIENT_DATA`/`AI_PENDING`; there are **no GET endpoints**. | Grading/scoring display; admin review |
| `app/underwriting/grading/params/sector_reference_v1.yaml` — 105 sector values | **Partial** | **Yes** (CEO review, not a vendor) | Marked `status: DRAFT_UNREVIEWED`, with `reviewed_by: null` on the top-level review block and on each of the 7 columns (provenance is per-column, not per-cell), header: *"CRITICAL — DO NOT WIRE THIS INTO grade()"*. **No loader exists** — `sector_reference.py` is required by an ACCEPTED spec and is absent, so the table is inert data. Consequence, from the spec itself: *"no real application can be scored — there is nothing to populate them from, so every application returns `AI_PENDING`."* Confirmed by direct call. | Grading/scoring display |
| `app/contracts` — `POST /contracts/` | **Partial** | Indirect (terms shape) | **No.** Creation from a LOCKED score run is real and the LOCKED gate is enforced. But `final_terms` is a copy of the mock (`{"mode": "default", "rate": "12%"}` — a *string* rate), `target_amount` is `requested_amount` verbatim with no relation to the engine's `target_payment_vnd`, and of the **six** states in the CHECK constraint only **two are reachable**: `ACTIVE_PENDING_FUNDING` (at creation) and `ACTIVE_FUNDED` (set from `app/market/`). `DRAFT`, `SIGNED`, `CLOSED`, `DEFAULTED` have no writer; `signed_at`/`activated_at` are never written. **Zero tests.** | Borrower + lender contract view |

## 1.4 Money movement

| Module / API | Status | Depends on pending partnership terms? | Interfaces/contracts stable? | User-facing use case(s) |
|---|---|---|---|---|
| `app/ledger` — double-entry ledger, custodial/ledger accounts, balance-by-sum | **Done** | **Yes, on account topology.** `custodial_accounts` enforces `scope IN ('PLATFORM', 'CONTRACT')`. VPBank **Option A** (one escrow per loan) maps onto `CONTRACT`. **Option B** — escrow in each *investor's own name*, which is FundLok's recommendation — is a **third topology the CHECK constraint does not permit**: a migration + remap, not a config change. ADR-003 anticipated the omnibus→escrow swap; it did not anticipate a per-beneficiary scope. | **Deliberately has no HTTP surface** (spec §4: *"internal service functions, not public HTTP endpoints"*). Nothing for the FE to build against — and **no read endpoint exists anywhere** to display a balance, a ledger entry, or a distribution history. | (indirect) all money flows |
| — *verification* | — | — | Genuinely complete and the strongest module in the repo. All 4 tables + partial unique indexes; DB immutability trigger present (`trg_ledger_entries_append_only`, `trg_ledger_transactions_append_only`, `BEFORE UPDATE OR DELETE`) and tested with raw SQL; cross-contract netting rejected (ADR-003's escrow invariant, enforced); balance computed as `SUM(credits) − SUM(debits)` with no stored column (asserted: `not hasattr(LedgerAccount, "balance")`). 13 tests, 1:1 with the spec's 13 acceptance criteria. | — | — |
| `app/payments` — `POST /disbursements`, `POST /repayments` | **Partial (shim)** → becomes **Blocked-on-partnership** | **Yes — heavily.** (a) **Settlement timing:** ADR-002 and the disbursement spec both mandate **202 Accepted**; the code returns **201** with a hardcoded terminal `status="RECORDED"`, a value in no spec. (b) **Rate/fee structure:** **no `FEE` leg is ever posted and no `FL_REVENUE` account is ever created** — 100% of gross repayment goes to lenders. The VPBank design settles the *mechanism* (fee travels inside a beneficiary instruction, never standalone, bank-verifiable as a proportion) but both **rates and both ceilings are still TBC**. (c) **Compliance flow:** dual-control (two FundLok signatories per instruction) is required by VPBank §3.3 B and does not exist — `/payments/*` is single-role ADMIN. | **No.** Expect rework on: 201→202; `DisbursementOut` gaining `bank_transaction_id`/`status: PENDING`; `RepaymentOut.balances` (mis-named — carries distribution legs, not balances) ceasing to sum to `amount` once the fee leg lands; new error codes; `Idempotency-Key` going from **optional to required**. `paid_at` is accepted and **silently discarded** — a back-dated repayment records today's timestamp. | Repayment tracking; disbursement (admin) |
| — *sub-finding* | — | — | **No `FUNDING` leg is ever posted either.** `place_order` marks the order FILLED and creates a `Holding` but never touches the ledger — so the borrower `DISBURSEMENT` debits an `OMNIBUS_CASH` account that was never credited, driving it permanently negative. Lender money is absent from the "legal record". | — |
| `app/banking` — `POST /banking/accounts/link`, `GET /banking/accounts`, `POST /banking/accounts/{id}/unlink` | **Blocked-on-partnership** (mock **by design**) | **Yes, definitionally.** Its own docstring: *"Stands in for a real Open API partner integration (Brankas or otherwise) that is not expected to happen."* Spec: *"mock-only until a partner is signed, at which point it is **replaced, not extended**."* | **Payload shapes are stable and deliberately partner-shaped** (masked reference, never the raw number) — the spec commits to callers not changing shape. But the *UX* is provisional: linking always succeeds synchronously with no pending state, where any real flow has consent/redirect/micro-deposits. `account_type`/`status` are bare `str`, so OpenAPI advertises no allowed values. | Lender funding; borrower disbursement account |
| — *sub-finding* | — | — | **The link is decorative.** Nothing consumes `LinkedAccount`: `place_order` has no linked-account check (deferred — it touches Phat-owned `app/market/`), and `/payments/disbursements` takes a free-text `bank_account`. Under the VPBank **closed-loop rule** ("whatever an investor receives can be paid out only to the account that investor originally funded from"), recording the originating account at funding time becomes a **hard requirement**, and `linked_accounts` is where it lands. | — |
| Brankas client, `bank_transactions`, `omnibus_balance_snapshots`, `POST /webhooks/brankas` | **Not built** | **Yes** | Spec'd in an **ACCEPTED** spec (`brankas-disbursement.md`) built entirely on a partner the docs say is dead. Zero of its 12 acceptance criteria are met. It names the vendor in a schema column (`brankas_transaction_id`) and an endpoint path. **It has not been marked SUPERSEDED** — an ACCEPTED spec currently describes tables and endpoints nobody intends to build as written. | — |

## 1.5 Marketplace & lending workflow

| Module / API | Status | Depends on pending partnership terms? | Interfaces/contracts stable? | User-facing use case(s) |
|---|---|---|---|---|
| `app/loans` — `POST /applications`, `POST /applications/{id}/submit` | **Partial** | No | Shapes are typed and thin, but the surface is incomplete: **no GET, no PATCH** — a DRAFT cannot be read back or edited. `LoanApplicationOut` omits `submitted_at`, `decided_at`, `decision_note`. Field naming is inconsistent: the request says `business_id`, the response says `project_id`, for the same value. | Borrower application |
| `app/projects` — `POST /projects`, `GET /projects`, `GET /projects/public` | **Partial** (2 defects) | No | **No.** `POST /projects` **500s** when an inline `loan_application` is supplied (`MissingGreenlet`). `GET /projects/public` is **empty for API-created projects** (seed data masks it). `ProjectWithApplicationOut` collapses N applications to a singular unordered `loan_applications[0]`. `GET /projects/{id}/applications` — the wizard's documented boot path — **does not exist**. | Borrower onboarding; lender browse |
| `app/sme` — `POST /businesses` | **Partial** (duplicate) | No | Duplicates `POST /projects` over the same service with a *narrower* response, while still silently creating and discarding a `LoanApplication`. Two ways to do one thing; one must be retired. | Borrower onboarding |
| `app/market` — `POST /listings` | **Partial**, **blocked in practice by GAP-1** | Indirect | Typed, but gated by `project_has_verified_kyc()`, which **can never return True through the API** — see GAP-1 below. Every test and the smoke script reach it with a direct ORM write. | Marketplace listing (admin) |
| `app/market` — `POST /listings/{id}/orders` | **Partial** → will be **reworked by the funding flow** | **Yes.** GAP-2 is the design note: *"the banking funding flow must introduce the real gap: order stays `PENDING_PAYMENT` until the lender's inbound payment confirms via bank webhook, then → `FILLED`."* Under VPBank the confirmation is a credit into the project escrow account (M1), and the **originating account must be recorded at that moment**. | **No — highest rework risk on the lender side.** Today `place_order` writes `status="FILLED"` and `payment_confirmed_at=now` unconditionally, with no payment gate. The fix changes the response, adds a pending state, and requires polling. **Also: `app/market/` has zero read endpoints** — no `GET /listings`, no listing detail, no orders list, no holdings. A lender cannot discover a listing id or see their own position through any API. | Lender funding |
| — *sub-findings* | — | — | Idempotency **is** implemented (unique column + replay returning the existing row) but the lookup is **not scoped by `investor_id`** — investor B replaying investor A's key against the same listing receives A's order row with 201. Also no `with_for_update()` on the listing read, so two concurrent orders can both pass the capacity check and overfund. Pro-rata `share_ratio` recomputation **is** implemented and correct, but is display-only (the money path recomputes from `principal`) and no endpoint exposes it. | — |
| `app/admin` — `GET /overview`, `GET /audit-logs` | **Partial** (1 blocking defect) | No | Well-shaped (generic `Page[T]` envelope, no N+1 on actor resolution) but **`GET /overview` 500s whenever any user has a NULL role** — the normal post-registration state — because `UserRow.role: str` is non-optional against a nullable column. **Read-only**: there is no mutation endpoint of any kind under `/admin` — no KYC approval, no user suspend, no role change, no listing lifecycle control. **Zero tests**, which is why the 500 is undiscovered. | Admin/ops console |

## 1.6 Planned modules that do not exist

Each is named in `CLAUDE.md` module ownership and/or the VPBank build list. Verified absent (`ls`, plus a grep of `app/**/*.py` returning zero hits for
`amortiz|repayment_schedule|share_conversion` — the terms appear only in docs). No ARQ, Celery or
Redis anywhere in the repo.

| Planned module | Status | Partnership dependency | Blocks which use case |
|---|---|---|---|
| `app/repayment_schedule` | **Not built** | **Yes, and its shape is now in question.** The VPBank model is a **daily revenue share**, not amortisation. `grading-engine-deviations.md` §D already asks whether an amortisation engine *"may not be on the critical path"* — the VPBank design suggests it is the wrong artefact entirely. | Repayment tracking |
| **T-VAN integration** (VPBank component 10) | **Not built, not started** | **Yes — a new, unsigned partner** not in any ADR or spec. Issues register #3: *"unbuilt and unconfirmed. Nothing appears in the repository."* Confirmed. It is *"a dependency of the money flow itself rather than a reporting convenience: without it there is no figure to collect against."* | Repayment tracking (all of it) |
| **Daily revenue-share engine** (component 11) | **Not built** | **Yes** — revenue-share % is Money-Flow open item #3 | Repayment tracking |
| **Dual-control payment instruction engine** (component 1) | **Not built** | **Yes** — VPBank §3.3 B requires two FundLok signatories per instruction | Disbursement, distribution |
| **Bank settlement records + reconciliation** (component 3) | **Not built** | **Yes.** FundLok has committed to building and operating reconciliation and producing daily evidence (issues register §3.1 item 3), and sign-off requires *"zero unmatched items over at least five days"*. | Admin/ops |
| **Collection matching** (4), **distribution engine** (5), **settlement account registration & verification** (6), **ops dashboards** (7), **exposure & reporting** (8), **data protection controls** (9) | **Not built** | Yes | Repayment, distribution, ops, compliance |
| `app/share_conversion` | **Not built** | Unclear — **no spec, no ADR, no data model at all** | Share conversion |
| `app/compliance` | **Not built** | **Yes** — ADR-004 is the only ADR still `Draft`; `docs/specs/compliance/` does not exist; the exposure-cap figure itself is unknown (OQ1) | Compliance reporting |
| **ARQ worker** | **Not built** (deferred) | No | Async grading, scheduled jobs |

## 1.7 The two recorded blockers, re-verified

Both `known-gaps.md` items are **still open**. I verified each independently rather than trusting the note.

**GAP-1 — no KYC approval path.** Confirmed, and worse than recorded. `Document.status` is written in
exactly two places in `app/`, both in `app/uploads/service.py`: `"PENDING"` and `"SCANNING"`.
All 20 occurrences of `APPROVED` in `app/` are accounted for and none is a write to
`Document.status` — `app/gverify/*` writes `STATUS_APPROVED` to **different tables** with no join to
`documents`; `app/underwriting/grading/*` is a `ScoreRun` decision; the rest are reads or an error string.
No admin mutation endpoint exists. So `project_has_verified_kyc()` can never return True through the
API, and `POST /market/listings` is unreachable in production. **Three separate breaks compound here:**
the only path that can create KYC `Document` rows is the mock-URL `/files/presign`; `SCANNING` has no
exit (no scanner exists); and there is no approval endpoint. The GVerify bridge that would fix this is an
open question in the eKYB spec (OQ4), not a decision.

**GAP-2 — orders auto-fill.** Confirmed. `status="FILLED"`, `payment_confirmed_at=now` at creation.
`PENDING_PAYMENT` exists only as the column default; `CANCELLED`/`EXPIRED` have no writer and no
endpoint.

**Dead states across the workflow** — of the documented state machines, reachable transitions are:
`LoanApplication` 3 of 5 (`APPROVED`/`REJECTED` have **no writer anywhere**; `decided_at` and
`decision_note` are never set) · `Contract` 2 of 6 · `Listing` 2 of 5 (`OPEN` at creation, `FUNDED` on full
funding; `DRAFT` never persisted, `CLOSED`/`CANCELLED` have no writer, and no endpoint opens, closes
or cancels a listing — though `open_at`/`close_at` are set as side effects) · `Order` 1 of 4 · `ScoreRun` 3 of 4, but `RUNNING` is never
observable (set and overwritten in one transaction).

---

# Part 2 — Flow readiness

Sources: the borrower-journey sentence in `CLAUDE.md`, the nine-step process in VPBank §3.1, and the
individual specs. Where the docs do not enumerate a flow, it is marked **GAP** — 11 of the 17 flows below have no
spec, and the repo contains **no end-to-end flow document at all**; `CLAUDE.md`'s one-sentence journey
is the only place the whole thing is traced.

Legend: 🟢 backed by Done + stable interface (build now) · 🟡 Partial (build with mock/stub, expect
rework) · 🔴 Blocked-on-partnership (skip or placeholder) · ⚪ not built

---

### FLOW 1 — Auth, registration & role selection
*Spec: none (enumerated in HANDOFF-01/02 as test names)*

| Step | Backed by | Status |
|---|---|---|
| Register (anti-enumeration 201) | `app/auth` | 🟢 |
| Email verification | `app/auth` + SMTP | 🟡 untested; 4 endpoints (verify-email, resend, forgot/reset password) have **zero tests** |
| Login → token pair + cookies | `app/auth` | 🟢 |
| Refresh with rotation + reuse detection | `app/auth` + `refresh_tokens` | 🟢 verified DB-backed: `token_hash` = sha256, `revoked_at` set on logout and on rotation, replay → 401 |
| Role selection (one-time, SME/INVESTOR) | `app/users` | 🟢 typed request, 11 tests |
| Google / Microsoft OAuth | `app/oauth` | 🟡 Google path skips audience validation; Microsoft 500s unless `MICROSOFT_CLIENT_ID` set; **zero tests** |

**Verdict: fully buildable today.** Two caveats: `GET /users/me` is untyped, and `secure=False` cookies
will need to change for the deployed HTTPS origin.

---

### FLOW 2 — Investor KYC onboarding (GVerify eKYC)
*Spec: `docs/specs/gverify/ekyc-kyc-verification.md` — **DRAFT**, but implemented and tested*

| Step | Backed by | Status |
|---|---|---|
| Submit ID front/back + portrait (base64) | `POST /gverify/kyc/verify` | 🟢 |
| Image validation (magic bytes, ≤10MB) | `app/gverify/service.py` | 🟢 |
| OCR both faces + confidence gate (≥0.85) | GVerify `verify-ocrid` | 🟢 |
| Face match (skipped if OCR failed — billing fail-fast) | GVerify `face-match` | 🟢 |
| Verdict APPROVED / REJECTED / FAILED, terminal in-request | `app/gverify` | 🟢 |
| Phone-QR handoff (desktop → mobile capture) | `POST /handoff`, `/handoff/verify` | 🟢 purpose-scoped 10-min JWT; wrong-purpose token → 401, tested |
| Read status | `GET /gverify/kyc/status` | 🟢 |
| **Downstream gating on KYC state** | — | ⚪ **GAP** — spec §2 explicitly out of scope: *"wiring loan/market gating to this table is a follow-up"* |

**Verdict: fully buildable end-to-end today.** The strongest flow in the codebase. Three things to know:
role gating is `INVESTOR`-only and is **undocumented in `FRONTEND_KYC_SPEC.md`**, so starting KYC
before role selection returns 403; there is **no frontend contract doc** for `/gverify/*`; and the vendor
is unsigned, so a demo runs on the demo tenancy.

---

### FLOW 3 — SME business verification (KYB)
*Spec: `docs/specs/gverify/ekyb-kyb-verification.md` — **DRAFT**, implemented and tested*

| Step | Backed by | Status |
|---|---|---|
| Submit business registration certificate | `POST /gverify/kyb/verify` | 🟢 (image or PDF) |
| OCR X decode (multipart) + confidence gate | GVerify | 🟢 |
| Tax code verify against Tổng Cục Thuế | GVerify `taxcode/verify` | 🟢 incl. a regression test on the outgoing wire body (lowercase `id`, else live `ERROR_01`) |
| Registry active-status check | `app/gverify/kyb_service.py` | 🟡 which values mean "active" is **unconfirmed** — code guesses two strings |
| Name cross-check (diacritic-insensitive) | `app/gverify/kyb_service.py` | 🟢 |
| Legal-representative ↔ KYC `person_number` match | flag-gated | 🟡 `GVERIFY_KYB_REQUIRE_REP_MATCH=False`, *"default off pending review"* |
| Resolve `MANUAL_REVIEW` | — | 🔴 **GAP** — *"an ops decision resolves it out-of-band"*: no endpoint, no actor, no SLA. A reviewed-and-accepted business **can never become approved** without a DB write |
| Satisfy the loan flow's KYC document requirement | — | ⚪ **GAP** = GAP-1. eKYB OQ4 asks whether an approved KYB should auto-approve it; unresolved |

**Verdict: buildable today for submit + verdict + status.** The `MANUAL_REVIEW` branch has no
resolution UI to build against, and nothing downstream consumes the result.

---

### FLOW 4 — Borrower loan application + document upload wizard
*Spec: `docs/FRONTEND_UPLOAD_SPEC.md` — most completely enumerated flow in the repo, but no status field, no owner, outside `docs/specs/`*

| Step | Backed by | Status |
|---|---|---|
| Create business (`POST /projects`) | `app/projects` | 🟡 **works only without an inline `loan_application`** — the combined call 500s (`MissingGreenlet`). Use the two-call path, or `POST /sme/businesses`, which calls the same service but discards the application before validation |
| Create application (`POST /loans/applications`) → DRAFT | `app/loans` | 🟢 |
| Wizard boot / resume — `GET /projects/{id}/applications?status=DRAFT` | — | 🔴 **endpoint does not exist.** Documented as the resume path; not registered. Closest substitute is `GET /projects` (eager-loads applications + documents) |
| Presign per file (`POST /uploads/init-upload`) | `app/uploads` + R2 | 🟢 real presign, deterministic key, 15-min TTL |
| Browser `PUT` to R2 | R2 | 🟢 |
| Replace a file (re-call init-upload) | `app/uploads` | 🟢 incl. `delete_object` on extension change |
| Confirm batch (`POST /uploads/confirm`) → HEAD-verify → `UPLOADED` | `app/uploads` | 🟢 idempotent, 1–20 keys |
| Submit (`POST /applications/{id}/submit`) → SUBMITTED | `app/loans` | 🟢 |
| Edit / read back a DRAFT application | — | ⚪ no GET, no PATCH on `/loans` |
| **Anything consuming the uploaded documents** | — | 🔴 **GAP, and it is the big one.** Per the grading specs: *"Document ingest and parsing (VAT declarations, Form B02-DN, CIC PDF)… Parsers are a separate future spec"* and *"**This is the largest remaining gap between here and production**"*. Six documents are collected; none is read by anything |

**Verdict: partially buildable — and close to fully.** All 6 upload steps are 🟢 and match the spec
exactly. Two fixes make this flow fully buildable: add `GET /projects/{id}/applications`, and either fix
the inline-application 500 or document the two-call path as canonical. Both are small and
partnership-independent. **No tests guard this contract**, so add them alongside.

---

### FLOW 5 — Grading / scoring & rate-tier assignment
*Specs: core + sector table **ACCEPTED**; integration **DRAFT** and explicitly "not yet an implementable plan"*

| Step | Backed by | Status |
|---|---|---|
| Admin starts score run (`POST /underwriting/score-runs`) | `app/underwriting` | 🟡 endpoint real, output **mocked** (72.50 / "B" / `{"mock": true}`) |
| Application → UNDER_REVIEW | side effect of the above | 🟡 no explicit review action drives it |
| 22-factor scoring → 4 premiums → grade → price → 8 gates | `app/underwriting/grading` | 🟢 **as a library** — verified against 10,000 rows, 0 failures. 🔴 **as a flow** — nothing calls it |
| Populate the 7 AI-supplied factors + sector CAGR | — | 🔴 no loader exists; every real application returns `AI_PENDING` (reproduced by direct call). `AI_SCORE_KEYS` has **7** members — the 6 sector factors **plus `founder`** — so a sector-table loader alone will not clear `AI_PENDING` |
| Persist `engine_version`, `params_version`, input snapshot for replay | — | ⚪ *"None of those columns exist"* |
| Gate 3 (low factor count) / Gate 7 (CIC floor) | config | 🔴 both ship **disabled** — Gate 3 fires on 98.4% of the golden set pending a business decision; Gate 7 pending the CIC scale |
| Admin approves → LOCKED | `POST /score-runs/{id}/approve` | 🟢 real, idempotent, READY→LOCKED enforced — **but untested** |
| Review queue with fired gates + evidence | — | ⚪ **GAP** — sketched in the DRAFT spec, unbuilt |
| Display grade / premiums / rate to borrower or lender | — | 🔴 no GET endpoint; response shape needs Phat's sign-off |

**Verdict: partially buildable — build the display against stubs, and expect the stub to become real
soon.** This is the flow where UI work and backend work should be sequenced deliberately: the
response shape is an open contract question, so a UI built against the current 2-field response
(`overall_score`, `risk_grade`) will be rebuilt. Agreeing the shape *first* — the integration spec says
exactly this — is cheaper than building twice. Note two shape traps: `overall_score` is `Numeric(5,2)`
and truncates 70.98376463 → 70.98 (recomputing the rate from it drifts the target payment by
hundreds of thousands of VND on a 3bn loan), and `risk_grade` holds `"B"` while requirements specify
*"0–100 nominal (no letter grades)"*.

---

### FLOW 6 — Contract creation
*Spec: **GAP — none exists***

| Step | Backed by | Status |
|---|---|---|
| Create contract from LOCKED score run | `POST /contracts/` | 🟡 real, LOCKED gate enforced |
| Populate `final_terms` | `app/contracts` | 🟡 copies the mock `{"mode","rate":"12%"}` |
| Funding target | `app/contracts` | 🟡 `= requested_amount`, unrelated to the engine's target payment |
| Loan agreement execution / signature (VPBank step 4: *"signed directly between investor and SME"*) | — | 🔴 **GAP.** `SIGNED` is unreachable; `signed_at` never written. Who signs, how signature is captured and evidenced — undocumented |
| ACTIVE_PENDING_FUNDING → ACTIVE_FUNDED | `app/market` on full funding | 🟡 reachable, but as a side effect of the auto-filling order |
| CLOSED / DEFAULTED | — | ⚪ no writer |

**Verdict: partially buildable** for a read-only contract summary. The signature step — which VPBank
step 4 makes a distinct accountable stage — has no spec, no schema support, and no code.

---

### FLOW 7 — Marketplace listing & browse
*Spec: **GAP — mentioned in passing only***

| Step | Backed by | Status |
|---|---|---|
| Publish listing (`POST /market/listings`) | `app/market` | 🔴 **unreachable in production** — GAP-1 gate |
| Investor browses listings | — | 🔴 **no read endpoint exists.** `GET /projects/public` is the nearest thing and returns projects, not listings — and is permanently empty |
| Listing detail | — | ⚪ not built |
| Open, close or cancel a listing | — | ⚪ no lifecycle endpoints. `OPEN` is written at creation and `FUNDED` on full funding; `min_ticket`/`open_at`/`close_at` are set, but only as side effects — `DRAFT`, `CLOSED` and `CANCELLED` have no writer |
| Provisional (unreviewed-sector) listings | — | 🔴 open question: *"Should `provisional: True` block publication to the marketplace, or only annotate it?"* |

**Verdict: blocked today, but not by a partnership** — by GAP-1 and by missing read endpoints. This is
the highest-value gap that FundLok can close entirely on its own.

---

### FLOW 8 — Lender funding / order placement
*Spec: **GAP** — the referenced `banking/brankas-investor-funding.md` does not exist; the intended design survives only as a bug report in `known-gaps.md`*

| Step | Backed by | Status |
|---|---|---|
| Acknowledge risk disclosure | `app/market` | 🟢 enforced |
| Place order (amount, min_ticket, capacity checks) | `app/market` | 🟡 real, but no `with_for_update()` → concurrent overfunding possible |
| Idempotency on order creation | unique `idempotency_key` | 🟡 works, but not scoped by investor — a replayed key can return **another user's order** |
| Require an ACTIVE linked account before funding | — | 🔴 deferred, needs joint agreement (Phat owns `app/market/`) |
| Record the **originating account** (VPBank closed-loop rule) | — | 🔴 **not built**, and it is a hard requirement of the VPBank structure |
| Order stays PENDING_PAYMENT until inbound payment confirms | — | 🔴 **the core of the rework.** Today it auto-fills |
| Lender transfers into project escrow (M1) | — | 🔴 partnership |
| `FUNDING` ledger leg | — | 🔴 type exists, **nothing posts it** |
| Holding + pro-rata `share_ratio` | `app/market` | 🟢 implemented and correct — but not exposed by any endpoint |
| Cancel / expire an order | — | ⚪ unreachable states, no endpoints |
| Lender sees their orders / holdings / position | — | ⚪ **no read endpoints at all** |

**Verdict: blocked on partnership for the money half; partially buildable for the commitment half.** A
"commit to fund" UI can be built now against the existing order endpoint, but the response contract
will change (pending state + polling), and the read endpoints a lender portfolio needs do not exist
yet — those are pure FundLok work and are not partnership-blocked.

---

### FLOW 9 — Escrow account provisioning (VPBank step 3)
*Spec: partially in `ledger-foundation.md` (the seam); the flow itself is **GAP***

| Step | Backed by | Status |
|---|---|---|
| Request restricted escrow account per loan | — | 🔴 partnership |
| Configure permitted-destination list | — | 🔴 partnership — **and this is the pivotal open question** (§3.3.2): yes to VPBank's blocked-account product = 29.5 man-days of config; no = 112.5 man-days of build |
| Configure dual-control instruction channel | — | 🔴 partnership |
| Record account against the loan | `custodial_accounts` | 🟡 **seam exists for Option A** (`scope='CONTRACT'`); **Option B needs a new scope** + migration |
| Internal ADMIN approval gate before an account goes live | — | ⚪ resolved in principle; needs an ops-portal control (Phat) with no spec |
| Close account at loan closure | — | ⚪ not built |

**Verdict: blocked.** Design a placeholder state. The one piece worth doing now is deciding whether
`custodial_accounts.scope` should be widened pre-emptively, given Option B is both FundLok's
recommendation and VPBank's understood preference.

---

### FLOW 10 — Disbursement
*Spec: `brankas-disbursement.md` — **ACCEPTED but vendor-dead**; VPBank M2/M3 supersede it in substance*

| Step | Backed by | Status |
|---|---|---|
| Verify preconditions (contract ACTIVE_FUNDED, listing FUNDED) | `app/payments` | 🟡 checks the **listing** but not `Contract.status == ACTIVE_FUNDED` (the spec requires both) |
| Omnibus/escrow balance pre-check | — | 🔴 not built; depends on whether the partner exposes a balance API |
| Dual-control instruction | — | 🔴 required by VPBank §3.3 B; not built |
| Bank executes to SME's verified account (M2) | — | 🔴 partnership |
| FundLok disbursement fee inside the same instruction (M3, ~1% of gross) | — | 🔴 **no fee leg exists in code at all** |
| Write `DISBURSEMENT` ledger entry | `app/payments` + `app/ledger` | 🟢 works — single-leg OMNIBUS_CASH → BORROWER, idempotent, cross-contract 409 |
| Async settlement (202 + webhook → SETTLED/FAILED) | — | 🔴 code returns **201** with hardcoded `"RECORDED"` |
| One disbursement per contract | — | 🔴 spec'd; **not enforced**, and a test currently locks in the opposite (two disbursements on one contract both return 201) |

**Verdict: blocked.** The ledger write is real and correct; everything that makes it a *disbursement*
rather than a bookkeeping entry is partnership-dependent.

---

### FLOW 11 — Daily revenue-share collection
*Spec: **GAP** — exists only in the VPBank proposal (§1.4 M4, §3.5.2 components 10–11), nothing in `docs/specs/`*

| Step | Backed by | Status |
|---|---|---|
| Pull prior-day invoice-level sales from a licensed T-VAN provider | — | 🔴 **not built, not started, partner not identified.** *"without it there is no figure to collect against"* |
| Compute amount due (% of revenue) | — | 🔴 the revenue-share % is unconfirmed (Money-Flow open #3). The grading engine *does* already emit `target_daily_vnd` and `daily_repayment_rate` on a 21-working-day/252-day convention — the arithmetic foundation exists |
| Issue payment request + notification | — | ⚪ not built |
| SME pays into escrow (VietQR) (M4) | — | 🔴 partnership; who bears the VietQR fee is unpriced |
| Match receipt → loan → day; route unattributable to an exception queue | — | ⚪ not built (component 4) |
| Track outstanding obligation against gross principal | — | ⚪ not built |

**Verdict: blocked, and the most under-built flow relative to its importance.** It is the product's actual
repayment mechanism and it has no spec in the repo, no code, and an unidentified partner. Worth a
spec now even with terms open — the T-VAN interface can be specified independently of VPBank.

---

### FLOW 12 — Allocation & distribution to lenders (+ FundLok fee)
*Spec: ledger primitives **ACCEPTED**; the flow is **GAP***

| Step | Backed by | Status |
|---|---|---|
| Compute each investor's pro-rata entitlement | `app/payments` | 🟢 principal-weighted; legs sum exactly to `amount` — one holding absorbs the residual (see below). The source comment calls this "largest-remainder-style"; it is not largest-remainder |
| Compose one instruction: N distribution legs + fee leg | `app/ledger` | 🟡 the ledger **supports** it (multi-leg, pass-through net-zero, and a test exercises a 4-leg split with a FEE to FL_REVENUE) — but `app/payments` posts **no fee leg** |
| Management fee inside the allocation (M6) | — | 🔴 rate and ceiling both TBC; no code |
| Rounding residual must not accrue to FundLok | `app/payments` | 🟡 **bound honoured, rule differs** — residual goes to the last holding by sorted UUID, not the largest holder. One-line change |
| Bank executes allocation (M5) | — | 🔴 partnership |
| Track each transfer individually; leave failures in escrow for retry | — | ⚪ not built (component 5) |
| Lender sees distributions received | — | ⚪ no read endpoint |

**Verdict: blocked for execution; the arithmetic is done.** Note `RepaymentOut.balances` currently
sums to the full repayment amount — once the fee leg lands, it will not, so any UI asserting that
breaks (a test asserts it today).

---

### FLOW 13 — Withdrawal / reinvestment (closed loop)
*Spec: **GAP** — VPBank §1.4 M7/M8 only*

| Step | Status |
|---|---|
| Balance available as soon as the day's allocation posts | 🔴 no balance read endpoint anywhere |
| Withdraw to the investor's **registered originating account only** | 🔴 partnership + the originating account is not recorded |
| Re-verification to change the registered account (not self-service) | ⚪ not built |
| Reinvest into a new loan (M8) | ⚪ not built |

**Verdict: blocked.** Worth noting the distinction the proposal draws — *availability* is daily,
*transfer* is on request — because it is a UI-visible concept with no backend support yet.

---

### FLOW 14 — Repayment tracking / schedule
*Spec: **GAP**; and the artefact itself is in question*

`POST /payments/repayments` accepts an arbitrary ad-hoc amount with **no schedule to reconcile
against**. There are no repayment-schedule tables, no due dates, no arrears or default states, and
`PENALTY` exists as a ledger type with no flow. `LoanApplication.repayment_preference` is stored and
**never read**. Under the VPBank model the "schedule" is a daily revenue-share obligation, so building
a classical amortisation engine may be building the wrong thing.

**Verdict: blocked, and needs a design decision before it is scoped.**

---

### FLOW 15 — Share conversion
*Spec: **GAP — total***

Five passing mentions across the entire repo and nothing else: no spec, no ADR, no data model, no
conversion ratio, no share class, no valuation basis, no cap-table integration, no legal instrument.
It also sits uneasily with ADR-004 D5 (*"no loan guarantees; FL is a pure marketplace, takes no
position"*) and `CLAUDE.md`'s *"FL does NOT take a position"* — no document addresses whether
issuing equity to lenders is inside the Certificate of Participation scope.

**Verdict: blocked on design, not on partnership.** The most economically consequential feature in the
product narrative has less documentation than the dev-environment ADR.

---

### FLOW 16 — Admin / ops review
*Spec: **GAP** — fragments across six documents*

| Step | Backed by | Status |
|---|---|---|
| Ops overview (users, projects, counts) | `GET /admin/overview` | 🔴 **500s whenever any user has a NULL role** |
| Audit log query | `GET /admin/audit-logs` | 🟢 works, typed, no N+1 |
| Approve/lock a score run | `POST /score-runs/{id}/approve` | 🟢 works (untested) |
| Trigger disbursement | `POST /payments/disbursements` | 🟡 works as a ledger write only |
| Maintenance mode | `app/system` | 🟢 |
| **Approve KYC documents** | — | 🔴 **does not exist** = GAP-1 |
| Approve/reject a loan application | — | ⚪ no writer for `APPROVED`/`REJECTED` |
| Resolve a KYB `MANUAL_REVIEW` | — | ⚪ not built |
| Suspend a user / change a role | — | ⚪ not built |
| Listing lifecycle controls | — | ⚪ not built |
| Reconciliation state + exception queues + escrow balances | — | ⚪ not built (component 7) |
| Approve a custodial account | — | ⚪ needs an ops-portal control, no spec |
| Four-eyes / dual control on instructions | — | 🔴 required by VPBank, not built |

**Verdict: partially buildable, and undervalued.** The audit log and score-run approval are real. Fixing
the `/admin/overview` 500 and adding a KYC document approval endpoint would unblock **two other
flows** (7 and 4) — the highest ratio of effort to unblocking anywhere in this audit. Note the ownership
seam: `app/admin/` is Phat-owned, but every admin action described lives in Edward-owned modules.

---

### FLOW 17 — Compliance reporting
*Spec: **GAP** — `docs/specs/compliance/` does not exist; ADR-004 is the only ADR still `Draft`*

Exposure caps (cap figure unknown), CIC integration (route undecided — direct membership vs via the
custodial bank vs a third party), regulatory reporting (no format, recipient, cadence or channel
documented), Circular 64 conformance (**neither banking spec cites Circular 64 or contains a single
C1–C5 acceptance criterion**), consent management (C4 — no spec, no table; `linked_accounts` has
`ACTIVE→REVOKED` but no time bound, scope, or consent artefact).

One item deserves flagging beyond engineering: ADR-004 D7/D8 require Vietnam-based IT systems and
no cross-border processing, while `docs/deployment/ci-cd-pipeline.md` §1 records the deployed region
as **`asia-southeast1` (Singapore)**. The VPBank proposal §4.4.6 discloses this proactively, and the
issues register marks it correct to do so. Nothing in the repo reconciles the two.

**Verdict: blocked.**

---

# Part 3 — Prioritisation

Ranked by (a) closeness to fully buildable and (b) demo value — how well the flow shows the product
independent of partnership specifics.

| # | Flow | Buildable today | Demo value | Why it ranks here |
|---|---|---|---|---|
| **1** | **SME KYB verification** (Flow 3) | ✅ Fully | **High** | Done, 24 tests, real registry cross-check against Tổng Cục Thuế. Visually compelling, entirely partnership-independent at the FL boundary, and it is the step a bank or regulator will ask about first. Skip the `MANUAL_REVIEW` branch. |
| **2** | **Investor KYC verification** (Flow 2) | ✅ Fully | **High** | Equal-strongest module (20 tests). The phone-QR handoff is a genuinely impressive demo beat. Needs a frontend contract doc written — the only real prerequisite. |
| **3** | **Auth + role selection** (Flow 1) | ✅ Fully | Medium | Table stakes but solid, and every other flow needs it. Type `GET /users/me` while you are in there. |
| **4** | **Borrower application + upload wizard** (Flow 4) | 🟡 Nearly | **High** | The most completely spec'd flow, real R2, contract matches implementation exactly. **Two small fixes make it fully buildable:** add `GET /projects/{id}/applications`, and fix or document-around the inline-application 500. Best effort-to-value ratio in the audit. Nothing consumes the documents yet — fine for a demo, not for production. |
| **5** | **Grading / rate-tier display** (Flow 5) | 🟡 Against stubs | **Highest** | The product's differentiator, and the engine is genuinely finished (10,000 rows, 0 failures). But it is unwired and the response shape is an open contract question. **Agree the shape with Phat first, then wire, then build UI** — building against today's 2-field mock guarantees rework. This is the fastest path to a second *substantive* flow and needs no partner. |
| **6** | **Admin / ops review** (Flow 16) | 🟡 Partly | Medium | Low glamour, high leverage: fixing the `/admin/overview` 500 and adding a KYC approval endpoint unblocks Flows 7 and 4. |
| **7** | **Marketplace browse + listing** (Flow 7) | 🔴 Blocked internally | **High** | Blocked by GAP-1 and by having **zero read endpoints** — but by nothing external. Once #6 lands, this becomes the most valuable lender-facing demo. Currently the largest self-inflicted gap. |
| **8** | **Lender commit-to-fund** (Flow 8) | 🟡 Commitment half | **High** | Build the commit UI now with a mock pending state; expect the response contract to change. The lender portfolio reads (orders, holdings, `share_ratio`) are pure FundLok work and are **not** partnership-blocked — worth doing. |
| **9** | **Contract summary** (Flow 6) | 🟡 Read-only | Medium | Buildable as a display; the signature step has no spec or schema. |
| **10** | **Disbursement** (Flow 10) | 🔴 Blocked | Medium | Ledger write real; everything else partnership. Design a placeholder/pending state. |
| **11** | **Allocation & distribution** (Flow 12) | 🔴 Blocked | Medium | Arithmetic done; fee leg and execution blocked. |
| **12** | **Daily revenue-share collection** (Flow 11) | 🔴 Blocked | **High if it existed** | The actual repayment mechanism, with no spec, no code, and an unidentified T-VAN partner. Highest ratio of importance to readiness. **Spec the T-VAN interface now** — it does not depend on VPBank. |
| **13** | **Escrow provisioning** (Flow 9) | 🔴 Blocked | Low | Placeholder only. Consider widening `custodial_accounts.scope` pre-emptively for Option B. |
| **14** | **Withdrawal / reinvest** (Flow 13) | 🔴 Blocked | Medium | Needs balance reads that do not exist. |
| **15** | **Repayment tracking** (Flow 14) | 🔴 Blocked | Medium | Needs a design decision (daily revenue share vs amortisation) before scoping. |
| **16** | **Share conversion** (Flow 15) | 🔴 Blocked on design | **High if it existed** | Needs a spec and an ADR before any estimate is meaningful. |
| **17** | **Compliance reporting** (Flow 17) | 🔴 Blocked | Low (external) | Needs counsel plus the CIC and partner decisions. |

**Suggested sequence, if the goal is a credible demo without partnership resolution:**
onboarding + KYC + KYB (1–3) → application wizard with its two fixes (4) → admin fixes (6) → wire the
grading engine after agreeing the shape (5) → marketplace browse (7) → lender commit with a mocked
pending state (8). That is a coherent borrower-to-lender story that ends exactly where the partnership
begins, which is the right place for it to stop.

---

# Part 4 — Gaps in flow enumeration

The user's brief asked for gaps to be flagged where flows are not fully enumerated. They are
substantial:

1. **No end-to-end flow document exists.** The one-sentence borrower journey in `CLAUDE.md` is the
   only place the whole thing is traced. Of its 11 steps, 4 have a complete ordered spec, 1 is spec'd as
   a mock, and 6 have none. No document sequences the handoffs *between* modules. The only
   document that does — the VPBank §3.1 nine-step process — is written for an external audience and
   is not part of the spec system.
2. **11 of the 17 flows below have no spec at all**: contract creation, marketplace listing, lender
   funding, escrow provisioning, daily revenue-share collection, distribution, withdrawal/reinvest,
   repayment tracking, share conversion, admin/ops, compliance.
3. **Referenced specs that do not exist**: `banking/brankas-investor-funding.md`,
   `banking/brankas-repayment.md`, a fee-deduction spec, `docs/specs/compliance/`, a
   document-ingest/parsing spec, a disbursement-flow spec (which owns the `SELECT FOR UPDATE`
   lock), a distribution spec, a share-conversion spec, an ops-portal spec.
4. **Missing ADRs that are explicitly called for**: the KYC provider decision (*"Needs an ADR"*), the
   Brankas pivot (`account-linking-mock.md` OQ1, *"Open — flagged, not resolved"*), the actual
   custodial partner and whether omnibus or escrow (ADR-003 promises it), and the "candidate ADR-008"
   cited in the grading core header. The index stops at 007 — and three of the seven ADRs are about a
   dev-only documentation search tool rather than the product.
5. **Two frontend contracts live outside the spec system** (`FRONTEND_KYC_SPEC.md`,
   `FRONTEND_UPLOAD_SPEC.md`) with no status, owner, or acceptance criteria — while `CLAUDE.md`
   mandates that all specs live in `docs/specs/<module>/<feature>.md` with nine required sections and
   that API contracts be defined in specs before either side implements. Meanwhile the two
   *most current* verification flows (`/gverify/*`) have **no** frontend contract at all.
6. **`brankas-disbursement.md` is ACCEPTED and describes a dead vendor.** It should be marked
   SUPERSEDED before someone implements it.
7. **`CLAUDE.md`'s phase tracker materially understates delivery** — it makes no mention of the
   underwriting/grading work (two ACCEPTED specs, engine merged), the GVerify modules (two DRAFT
   specs, 1,352 LOC, 44 tests), or `account-linking-mock.md` (implemented). `docs/database/erd.md` is stale for the same reason —
   it records head `6f3a29bbd701` and 22 tables, three revisions and two tables behind. It also lists Phase 0 as "(complete)" with an unchecked
   item, and marks the `app/files/` cleanup `[x]` while `files_router` is still mounted.
8. **`app/gverify/` is not in `CLAUDE.md`'s module ownership table**, is absent from the ERD, and has
   zero `GVERIFY_*` variables in the CI/CD doc — despite being the largest verification subsystem.

---

# Part 5 — Partnership dependency register

Consolidated for the matrix's column 3.

| Partner | Status | Modules affected | What specifically could change |
|---|---|---|---|
| **VPBank** (custodial escrow) | **Live conversation; unsigned.** Proposal bundle dated 5 Aug 2026. Pivotal open question §3.3.2 (blocked-account product + bank-enforced destination list) = 29.5 vs 112.5 man-days. | `app/ledger`, `app/payments`, `app/banking`, `app/market` (orders), future compliance + ops | **Account structure** (Option A per-loan escrow vs Option B per-investor escrow — Option B needs a new `custodial_accounts.scope`) · **Rate/fee structure** (management fee rate, both registered ceilings, revenue-share %, per-transaction/per-account/minimum-balance pricing — the register quantifies Option B at ~1.06bn VND/yr in transaction fees at month 12 at mid-range pricing) · **Compliance flow** (dual control, permitted-destination list, daily statement, three-way reconciliation with zero unmatched items over 5 days) · **Settlement timing** (201→202, async confirmation) · **Interest on escrow balances** (unresolved; FundLok's position is it belongs to beneficiaries) |
| **T-VAN provider** (licensed sales data) | **Not identified, not started.** Issues register #3. | (unbuilt) daily revenue-share engine | Everything — this is a dependency of the money flow itself. Data schema, invoice granularity, latency, pricing, and whether daily pull is even supported |
| **Brankas / Gimasys** | **Not happening** (2026-07-07 decision). ADR-002 still says ACCEPTED. | `app/banking` (mocked indefinitely) | Historical. The risk now is that an ACCEPTED spec names this vendor in a schema column and an endpoint path |
| **GVerify / Datatrust / PATK** | **Demo tenancy only; unsigned.** No real credentials; `GVERIFY_BASE_URL` has no default. | `app/gverify` (eKYC + eKYB) | **Rate/fee structure** — per-call billing *drives control flow* (fail-fast ordering exists to avoid billable calls) · **Data schema** — already proven unstable; code follows verified live samples over the v2.5.1 doc · **Compliance flow** — liveness unresolved; FL applies *no* face-match threshold of its own, delegating the verdict to the vendor's boolean, so a vendor retune changes FL's approval rate with no code change · **PII retention** — ID images and certificates now retained in R2 (a v1.1 reversal of v1.0's no-retention stance) with no ADR and no Decree 94 privacy analysis |
| **Didit** | **Live and default, but slated for possible replacement.** No provider ADR. | `app/verification` | Whether it is retained at all. If dropped: `/kyc/*`, `/kyb/*`, two tables, and `FRONTEND_KYC_SPEC.md` all become dead weight |
| **CIC** (credit bureau) | **Required by Decree 94; route undecided** — direct membership vs via the custodial bank vs a third party (ADR-004 OQ2). This couples CIC to the VPBank outcome. | `app/underwriting`, future compliance | **Data schema** (a structured feed vs today's hand-entered scalar from an uploaded PDF) · **Scale** (0–700 vs 150–750 — unresolved; Gate 7 disabled because of it) · **Compliance flow** (consent chain, licensing) · quantified pricing impact: Behavioral is 14.7% of the rate spread |
| **Tổng Cục Thuế** (tax registry) | **Indirect, via Datatrust.** No direct relationship. | `app/gverify` (eKYB) | If the GVerify deal does not land, the strongest external truth-source in KYB disappears and KYB reverts to document-OCR only |
| **GSO / SBV** (sector reference data) | **"TO BE CONFIRMED"** | `app/underwriting` sector table | 105 values ship `DRAFT_UNREVIEWED`. Sector drives 36% of the rate spread; a 10-point error in one column is ~30bp on every loan in that industry |
| **Loc (CEO)** — not a vendor, but a blocking dependency | 9 open decisions (D19–D27) plus sector-table OQ1–OQ4, all targeted "Post-E2E" | `app/underwriting` | Gate 3 threshold, CIC scale, loss-making treatment, owner-withdrawal scale, AI rubrics, and review of all 105 sector values |

---

# Part 6 — Defects and cleanups surfaced (not previously recorded)

Listed because each affects UI planning. None is in `known-gaps.md`.

**Blocking**

1. `GET /admin/overview` → **500** when any user has a NULL role (`UserRow.role: str` vs nullable column; also `AdminStats.users_by_role` gets a `None` key). Breaks every mode of the admin console's only data endpoint.
2. `POST /projects` with an inline `loan_application` → **500** `MissingGreenlet` (implicit lazy load of `LoanApplication.documents` after `db.refresh` under `AsyncSession`).
3. `GET /projects/public` → **always `[]`** (`create_project` hardcodes `DRAFT`; the query filters `ACTIVE`; nothing ever writes `ACTIVE`).
4. `GET /projects/{project_id}/applications` — documented as the upload wizard's boot/resume path, **not implemented**.
5. `/files/presign` returns a fabricated URL to `mock-storage.fundlok.local` — the only path that can create KYC `Document` rows.

**Correctness / security**

6. Order idempotency lookup is **not scoped by `investor_id`** — a replayed key can return another user's order row (cross-tenant leak). Also unscoped by payload, so a replay with a different amount silently returns the original.
7. `place_order` has **no row lock** — concurrent orders can overfund past `target_amount`.
8. Google OAuth `verify_token` uses the userinfo endpoint with an access token and **never validates audience or issuer**, so a token minted for a different Google client is accepted; `GOOGLE_CLIENT_ID` is effectively unused for Google.
9. `get_current_user` does not check `user.status` or `email_verified` — a `SUSPENDED` user authenticates normally.
10. Password reset does **not** revoke outstanding refresh tokens, and reset/verification tokens are stateless and replayable within their windows.
11. Didit webhook: the dedupe row for an unknown `session_id` is **never committed** (the router commits only inside `if verification is not None`), so those deliveries reprocess on every redelivery. A payload with no `event_id` bypasses dedupe entirely.
12. `app/verification` still uses a **sync** `httpx.Client` inside async handlers — blocks the event loop (documented, deferred). Same pattern in `app/utils/captcha.py` and `boto3` calls reached from three `async def` handlers in `app/users/router.py`.
13. `RepaymentCreate.paid_at` is accepted and **silently discarded** — back-dated repayments record `now()`.
14. `_first_entry_of_type` can return `None` on an idempotent replay path → unguarded `AttributeError` → 500.

**Cleanups**

15. `app/schemas/` is dead (0-byte + fully commented-out files, imported nowhere). `UserCreate`/`UserResponse` in `app/users/schemas.py` are also unused and contradict live registration behaviour.
16. `app/sme` duplicates `app/projects`; `/files/*` duplicates `/uploads/*`. HANDOFF-02's acceptance criterion — *"Remove `app/files/` **and its `files_router` include from `app/main.py`**"* — is unmet: the directory is gone, the routes are live.
17. `LINKED_ACCOUNT_STATUSES` is declared and unreferenced; `DiditWebhookPayload` is never imported (the webhook parses raw bytes inline). `scripts/check_sector_reference.py`, which the sector YAML instructs the reader to re-run after any edit, does not exist.
18. `scripts/test_all_endpoints.py` is stale — calls `PUT /users/me/role`; the route is `PATCH`, so it 405s at step 8a.
19. `tests/alembic/` is an empty directory. `app/payments` tests live under `tests/lending/` — there is no `tests/payments/`, contrary to the stated convention.
20. Python version drift: CI tests on 3.11, the deployed container runs 3.12-slim.

**Test coverage map** (26 test modules): strong on `app/gverify` (44 tests), `app/ledger` (13, exactly
1:1 with the spec's 13 criteria), `app/banking` (8, exactly 1:1), `app/auth` (15). **Zero tests** on `app/verification`,
`app/uploads`, `app/oauth`, `app/admin`, `app/system`, `app/contact`, `app/contracts`, and
`app/underwriting`'s service/router layer (the grading *library* is heavily tested; the endpoints
around it are not).

---

## Closing note

The shape of the codebase is better than the phase tracker suggests, and unevenly so. Three
subsystems are genuinely production-grade — the double-entry ledger, the GVerify verification
modules, and the grading engine — and two of the three are not connected to anything a user can
reach. The gap between "built" and "reachable" is where most of the remaining value sits, and almost
none of that gap is partnership-blocked: GAP-1, the missing read endpoints, the admin 500, and the
grading wiring are all work FundLok can do entirely on its own while VPBank answers §3.3.2.
