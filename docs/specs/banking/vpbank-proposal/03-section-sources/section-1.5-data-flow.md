# 1.5 Data flow

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

**FundLok moves data and instructions, not money.** Funds move only between the parties' own accounts and the restricted escrow account held at VPBank; at no point does money pass through an account controlled by FundLok. What FundLok moves is information: the appraisal that produces a loan, the instruction that asks the bank to release funds to a permitted destination, and the reconciliation that proves the two records agree.

This section sets out every category of data that crosses the boundary between FundLok and VPBank, in which direction, and — equally important — what deliberately never crosses it. The governing principle is **minimum necessary**: VPBank receives what it needs to open an account, execute an instruction and report what it did, and nothing beyond that.

Three properties of the design follow from that principle and are visible in the inventory below.

First, **credit information never reaches VPBank.** VPBank makes no lending decision, so it has no need for a credit score, a grade, a rate tier or an SME's financial statements, and it receives none of them. This is what makes the statement "VPBank takes no credit risk" a structural fact about the data as well as a contractual one.

Second, **due diligence data does not route through FundLok.** Each party submits its account-opening documentation directly to VPBank for the bank's own customer due diligence. FundLok neither collects that set on VPBank's behalf nor transmits it, because the bank's assessment is the bank's own and is not built on FundLok's records.

Third, **instructions carry no more personal data than a named bank transfer requires** — an account number, a holder name, an amount and a reference.

---

## 1.5.1 The boundary

| Zone | Holds | Boundary behaviour |
|---|---|---|
| Parties — investor and SME | Their own identity, financial and settlement-account data | Submit platform data to FundLok; submit account-opening documents directly to VPBank |
| FundLok — arranger and servicer | Platform records, appraisal, ledger, instruction history, reconciliation state | Sends instructions and account-provisioning data to VPBank; receives confirmations and statements. Never holds funds |
| VPBank — custodian | The escrow account, its permitted destinations, and the record of what it executed | Receives instructions; returns outcomes, statements and balances. Holds no credit information |

---

## 1.5.2 Full inventory — data exchanged with VPBank

### FundLok → VPBank

| Ref | Exchange | Fields |
|---|---|---|
| F1 | Account provisioning request | Loan reference · requested account title · permitted-destination list, each entry carrying destination account number, account-holder name, bank identifier and destination type (verified borrower account, or registered investor originating account) · identity of the requesting authorised user |
| F1a | Permitted-destination amendment | Loan reference · escrow account number · entry to add or remove · authorising users · reason code |
| F2 | Payment instruction, per transfer | Escrow account number · destination account number and holder name · amount · currency (VND) · unique FundLok instruction reference · batch reference · requested value date · narrative to appear on the beneficiary's statement · identity of the two authorising users |
| F3 | Channel administration | Authorised user names and roles · entitlement level (prepare or approve) · additions, amendments and revocations |
| F4 | Account closure request | Loan reference · escrow account number · confirmation of nil balance · authorising users |

### VPBank → FundLok

| Ref | Exchange | Fields |
|---|---|---|
| B1 | Account provisioning confirmation | Escrow account number · account title as registered · status · opening date |
| B2 | Instruction outcome | Batch acknowledgement · per-transfer status · bank reference per executed transfer · rejection reason code and text where applicable · execution timestamp |
| B3 | Daily statement, per line | Bank transaction identifier (stable across retrievals) · booking date · value date · amount · direction, credit or debit · counterparty name · counterparty account · payment reference or narrative as received · running balance |
| B3a | Statement header | Escrow account number · statement period · opening and closing balance |
| B4 | Balance enquiry response | Escrow account number · balance · timestamp |
| B5 | Final statement on closure | Full transaction history for the account · nil closing balance · closure date |

### Parties → VPBank, directly

| Ref | Exchange | Fields |
|---|---|---|
| V0 | Account-opening documentation for the bank's own due diligence | As specified by VPBank — identity documents, enterprise registration, beneficial ownership and authorised signatories. **FundLok does not collect, hold or transmit this set on VPBank's behalf** |

### Parties ↔ FundLok — recorded for completeness, none of which crosses to VPBank

| Ref | Exchange | Fields |
|---|---|---|
| P1 | Identity and enterprise data | Identity verification result and supporting documents · enterprise registration and licence data · authorised representative identity |
| P2 | Financial and appraisal inputs | Financial statements · trading history · sector classification · personal guarantee terms |
| P3 | Settlement account and consent | Settlement account details, stored masked · consent record with timestamp, scope and withdrawal state |
| P4 | Returned to the parties | Loan terms and rate · daily amounts requested and collected · statements and holdings · settlement confirmations |
| P5 | Daily sales data, via a licensed T-VAN provider | Invoice-level sales records for the prior day, from which the daily revenue-share amount is computed. Sourced from the borrower's e-invoice data with the borrower's consent, not from VPBank |
| P6 | Daily payment request to the borrower | Amount due · reference to quote · issued through the FundLok platform and its notification channel |


---

## 1.5.3 What never crosses to VPBank

- Credit score, grade, rate tier, or any appraisal output or working.
- SME financial statements or supporting documentation.
- Personal guarantee terms or any enforcement detail.
- Investor portfolio holdings, allocation preferences or platform behaviour.
- Borrower sales and invoice data obtained through the T-VAN provider, and any personal data of the borrower's own customers contained in it.
- Identity documents and verification evidence held by FundLok for its own onboarding.
- Any personal data beyond the account number, holder name, amount and reference that a named transfer requires.

This list is a design constraint, not an aspiration. Its practical consequence is that a compromise of the FundLok–VPBank interface would expose transfer instructions and statements, not the personal and credit data of the platform's users.

---

## 1.5.4 Handling and lawful basis

Personal data crossing to VPBank is limited to what is necessary to perform the loan contract and the custodial arrangement. Consent is captured from each party at the point their settlement account is registered, is recorded with timestamp and scope, and can be withdrawn. Transport is encrypted, access is restricted to named authorised users with separated prepare and approve entitlements, and every exchange in the inventory above is logged on both sides. Retention, encryption standards, breach response and the treatment of any processing outside Vietnam are specified in Section 4.4.

---

## 1.5.5 Diagram

The accompanying diagram shows the three zones, every flow in 1.5.2 with its reference, and the panel of data that never crosses. The flow from the parties directly to VPBank is drawn dashed and routed around FundLok, to make visible that the bank's due diligence does not pass through the platform. The T-VAN sales feed (P5) and the daily payment request (P6) are FundLok-side flows that do not cross the VPBank boundary, so they appear in the inventory above and in the diagram's non-crossing panel rather than as boundary flows.

*[Insert: `section-1.5-dataflow` — three-zone data-flow diagram with flow references and the non-crossing set.]*

---

## 1.5.6 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | VPBank's required field set and format for F1, F2 and F3 | The inventory above is FundLok's proposal; VPBank's channel will impose its own schema | VPBank, requested by Edward | Pending VPBank confirmation |
| 2 | Maximum length of the payment reference preserved end to end, and whether the counterparty name is always returned on inbound credits | Determines whether inbound credits can be attributed automatically or fall to manual investigation. Same dependency as Section 3.3 items C3 and D2 | VPBank, requested by Edward | Pending VPBank confirmation |
| 3 | Whether VPBank requires any beneficiary information beyond the permitted-destination entries in F1 | If it does, the minimisation position in 1.5.3 needs restating and Section 4.4 needs to cover the additional set | VPBank, requested by Edward | Pending VPBank confirmation |
| 4 | Whether account-opening documentation (V0) is submitted in branch, through VPBank's own digital channel, or by a route FundLok needs to signpost | Affects the party experience at Step 1 of Section 3.1 but not the data boundary itself | VPBank, requested by Edward | Pending VPBank confirmation |
| 5 | Account structure selected in Section 1.8 | If individual per-party accounts are adopted, F1 and B1 apply per party rather than per loan; field sets are unchanged | Loc + Edward | 2026-08-12 |
| 6 | Whether invoice-level data received through the T-VAN provider contains personal data of the borrower's own customers, and if so what is retained | A new category of personal data that no section previously considered. Bears directly on Section 4.4 | Edward, with counsel | 2026-08-14 |
| 7 | The notification channel used for the daily payment request, and what data it carries | Determines whether a further processor sits in the flow and what Section 4.4 must cover | Edward | 2026-08-12 |

---

*Dependencies: Section 1.3 (four-sided structure). Consistent with Section 1.4 (money flow), Section 3.1 (process), Section 3.3 (Phase 1 requirements) and Section 4.4 (data protection).*
