# 4.4 Data protection and information security

*[CONTENT — Edward. English draft for internal review; Vietnamese version to follow.]*

---

FundLok processes personal data of investors and of the representatives of borrowing enterprises. This section sets out the legal framework FundLok operates under, the controls in place, and the controls still to be completed before go-live.

The governing instrument is **Law No. 91/2025/QH15 on Personal Data Protection**, which took effect on **1 January 2026** (source: Law on Personal Data Protection No. 91/2025/QH15, National Assembly, 2025). It is in force now, not pending. Two of its provisions bear directly on this arrangement: breach notification is required **within 72 hours of detection**, and for a financial service provider that notification extends to the affected data subjects and not only to the regulator. The law also carries sector-specific safeguards for financial, banking and credit activities, with detail to follow in implementing regulations.

Nothing in this section asks VPBank to accept responsibility for FundLok's data protection obligations, and FundLok does not offer its own controls as a substitute for any assessment VPBank performs on its own account.

**Where this section states a commitment rather than a current state, it says so.** Items 3 and 4 of 4.4.10 are commitments with a trigger, not descriptions of today.

---

## 4.4.1 Personal data processed

| Category | Examples | Source | Crosses to VPBank |
|---|---|---|---|
| Identity data | Name, date of birth, national identifier, address, contact details | The individual | Name only, as part of a permitted-destination entry or a transfer instruction |
| Identity evidence | Identity document images, and the biometric facial comparison performed during verification | The individual, via a third-party verification provider | No |
| Enterprise data | Business registration, licence data, authorised representative identity | The SME | Name only, as above |
| Financial data | Financial statements, trading history, appraisal inputs and outputs | The SME | No |
| Settlement data | Bank or e-wallet account details, held masked | The individual or enterprise | Account number and holder name, as required for a named transfer |
| Platform data | Commitments, holdings, repayment history, access logs | Generated in use | No |
| Borrower sales data | Invoice-level sales records for the prior day, drawn from the borrower's e-invoice data through a licensed T-VAN provider, from which the daily repayment amount is computed | The borrower's e-invoice records, with the borrower's consent | No |
| Consent records | Scope, timestamp, withdrawal state | Generated in use | No |

The set that crosses to VPBank is limited to what a named bank transfer requires, and is specified in full in Section 1.5.2. The biometric facial comparison performed during verification is the most sensitive category FundLok handles; it is not shared with VPBank and is addressed specifically at 4.4.5.

**Borrower sales data requires its own treatment, and it is new.** The daily revenue-share mechanism in Section 1.4 depends on reading each borrower's prior-day sales through a licensed T-VAN provider. Invoice-level sales records are principally the borrower's own commercial data, but where the borrower sells to individuals those records may also contain personal data belonging to **the borrower's own customers** — people who have no relationship with FundLok and have given FundLok no consent. FundLok's position is that it needs only aggregate daily revenue, not counterparty detail, and that the integration should therefore either not request invoice-level counterparty fields or discard them on receipt rather than store them. Whether the T-VAN interface permits that separation is an open item at 4.4.10, and it is far cheaper to design out now than to justify later.

---

## 4.4.2 Consent mechanism

Consent is obtained at the point of collection, separately for each purpose, and is never bundled into acceptance of the platform terms as a whole. Each consent record carries its scope, the version of the notice presented, a timestamp, and its withdrawal state; the records are held in the platform and are auditable.

Consent is obtained separately for identity verification, including the biometric comparison, and for the registration of a settlement account and its use as a transfer destination. A party can withdraw consent through the platform. Where consent is withdrawn for a purpose that is a precondition of an active loan, FundLok can no longer act for that party prospectively but retains the records the loan and the law require — see 4.4.4.

Not all processing rests on consent. Processing necessary to perform the loan contract and the management authorisation contract rests on that contractual necessity, which Law 91/2025 recognises as a basis distinct from consent. FundLok's position is that this is the correct basis for instruction issuance, reconciliation and record retention, and it is one of the items for counsel confirmation at 4.4.10.

---

## 4.4.3 Access control

| Control | Implementation | Status |
|---|---|---|
| Role-based access control | Every platform endpoint authorises against the caller's role; no endpoint relies on client-side restriction | In production |
| Authentication | Token-based authentication with separate access and refresh tokens, and server-side revocation so a session can be terminated | In production |
| Credential storage | Passwords stored using Argon2 hashing; no reversible credential storage anywhere | In production |
| Least privilege | Staff access is granted per role, and access to personal data is limited to the roles that require it | In production, formal review to be documented |
| Separation of duties on money movement | Preparation and approval of a payment instruction are held by different named individuals, enforced by VPBank's channel entitlements rather than by FundLok's procedure | To be built — Section 3.5, component 1 |
| Revocation | Platform access and banking-channel entitlement are both withdrawn on a personnel change, on the same day | In production for the platform; banking channel per Section 3.3 item E2 |
| Secrets management | Application secrets held in a managed secret store, never in source control or configuration files | In production |
| Audit logging | Administrative and financial actions recorded to an append-only log; the ledger itself cannot be edited or deleted at either the application or the database layer | In production |

---

## 4.4.4 Retention

FundLok retains loan and transaction records, and the personal data necessary to interpret them, for **ten years from loan closure**. The period is set to align with the retention obligation applicable to accounting and financial records under Vietnamese law; the precise statutory basis is for counsel to confirm.

Categories held for shorter periods: identity evidence, including document images and the biometric comparison result, is retained only for as long as required to evidence that verification was performed, and the underlying images are not retained beyond that need. Access and session logs are retained for two years. Consent records are retained for the life of the relationship plus the ten-year period, because a consent record is the evidence that processing was lawful and must outlive the processing itself.

Retention and erasure interact, and the position should be stated rather than left implicit. Where a data subject requests erasure, FundLok deletes what it holds on consent and no longer needs. It does not delete records it is required by law to retain, or that are necessary to evidence a loan that existed — a completed loan cannot be unwound because one party later asks for its record to be removed, and the other party to that loan has its own interest in the record. FundLok's response to an erasure request therefore distinguishes the two sets and explains which is which.

At the end of the retention period records are deleted, and deletion is logged.

---

## 4.4.5 Biometric and sensitive data

The verification process includes a facial comparison between a submitted image and the identity document. This produces biometric data, which Law 91/2025 treats with heightened protection — and it is specifically one of the categories for which a breach must be notified to the affected individuals, not only to the regulator.

FundLok's position: the biometric comparison is performed by a specialist third-party verification provider acting as a processor on FundLok's instruction; the comparison result is retained as evidence that verification occurred; the underlying images are not retained beyond the need described in 4.4.4; and the data is not shared with VPBank at any point.

**One matter is open and material.** If the verification provider performs any part of that processing outside Vietnam, it is a cross-border transfer of biometric data and requires a transfer impact assessment, and it also sits in tension with the localisation commitment at 4.4.6. FundLok has flagged this rather than assumed it resolved — item 5 of 4.4.10.

---

## 4.4.6 Data localisation

**Commitment.** FundLok will process and store personal data relating to this arrangement within Vietnam, and will complete the migration to in-country hosting **before go-live** — that is, before Stage 3 of Section 3.7, the first live loan.

Stated plainly, because a bank should not have to infer it: FundLok's platform currently runs in a managed cloud region in South-East Asia outside Vietnam, with object storage on a globally distributed provider. That is the present state, and it is why this is written as a commitment with a trigger rather than as a description. The migration covers the application runtime, the database, object storage holding uploaded documents, and backups.

Law 91/2025 does not itself impose a general localisation requirement on all personal data. FundLok's commitment is therefore made as a matter of policy and of assurance to VPBank, and to remove any question about where data relating to a Vietnamese custodial arrangement is held. Whether any additional statutory localisation obligation applies to this activity is for counsel to confirm.

---

## 4.4.7 Encryption

| Layer | Standard |
|---|---|
| Data at rest — database, object storage, backups | **AES-256**, applied by the managed platform to all stored data and backups |
| Data in transit — party to platform, platform to VPBank, platform to processors | **TLS 1.2 or above**, with weaker protocol versions and cipher suites disabled |
| Credentials | Argon2 password hashing; application secrets in a managed secret store, encrypted at rest |
| Settlement account details | Stored masked; the full account number is used to compose an instruction and is not persisted in full |
| Document access | Time-limited pre-signed access to object storage; documents are not served from long-lived public URLs |

---

## 4.4.8 Breach response procedure

Law 91/2025 requires notification within **72 hours of detection**, and for a financial service provider that extends to affected data subjects. FundLok's procedure is built to that clock, working backwards from it.

1. **Detection and logging.** Any suspected incident is recorded on detection with the detection timestamp, which starts the 72-hour period. The timestamp is recorded first, before assessment begins, so the clock is never reconstructed after the fact.
2. **Containment.** Immediate steps to limit exposure — revoking credentials or tokens, disabling an affected integration, isolating a component. Containment does not wait for the assessment to complete.
3. **Assessment.** Within 24 hours of detection: what data, whose, how many, what cause, whether it is ongoing. Any incident touching biometric data, identity evidence or settlement data is treated as notifiable unless assessment positively establishes otherwise.
4. **Notification.** To the regulator within 72 hours of detection. To affected data subjects within the same period where the incident involves their data, in plain language, describing what happened, what data was involved, what FundLok has done, and what the individual should do.
5. **Notification to VPBank.** Where an incident affects the integrity of instruction data, the escrow arrangement or any data exchanged with VPBank, FundLok notifies VPBank without waiting for the regulatory deadline. FundLok asks VPBank to reciprocate, so that each party's 72-hour clock can be met — item 6 of 4.4.10.
6. **Remediation and record.** Root cause addressed, and the incident, timeline, decisions and rationale recorded. The record is retained whether or not the incident was notifiable, because the decision not to notify must itself be evidenced.
7. **Review.** Each incident is reviewed for whether the impact assessment at 4.4.9 needs updating.

A named individual is accountable for running this procedure. The procedure is tested rather than merely written: FundLok runs a tabletop exercise against it before go-live.

---

## 4.4.9 Impact assessments and accountability

Law 91/2025 requires a data processing impact assessment, and a transfer impact assessment where personal data is transferred across borders, with reassessment when the processing changes. It also requires an organisation to designate a data protection function, internally or through an external provider. Small businesses and startups have a five-year exemption from the impact assessment requirement.

FundLok's position:

- A **data processing impact assessment** covering the platform, the verification provider and the VPBank exchange will be completed before go-live, and reviewed on any material change to processing.
- A **transfer impact assessment** will be completed for any processing that occurs outside Vietnam, including by the verification provider, and will be closed out by the migration at 4.4.6 where the transfer ceases.
- A **designated data protection responsibility** is assigned to a named individual, with external counsel engaged for the legal assessment.
- FundLok will **not rely on the small-business exemption** unless counsel advises that it clearly applies. Producing the assessments is useful discipline regardless of whether the exemption is available, and relying on an exemption whose applicability is uncertain is a poor position to hold in front of a banking partner.

FundLok also notes the prohibition in Law 91/2025 on trading personal data, and states for the record that FundLok does not sell, license or otherwise trade personal data, and does not use investor or borrower personal data for any purpose beyond operating the platform and the loans on it.

---

## 4.4.10 Items to be confirmed

| # | Item | Why it matters to this section | Owner | By |
|---|---|---|---|---|
| 1 | Precise statutory basis for the ten-year retention period | Stated in 4.4.4 as aligned with accounting-record retention; the citation must be exact before this goes to VPBank | Edward, with counsel | 2026-08-14 |
| 2 | Lawful basis analysis — which processing rests on consent and which on contractual necessity | Determines whether withdrawal of consent can halt processing needed to service an active loan | Edward, with counsel | 2026-08-14 |
| 3 | Migration of application runtime, database, object storage and backups into Vietnam | 4.4.6 is a commitment, not a current state. Must complete before Stage 3 of Section 3.7 | Edward | Before go-live |
| 4 | Separation-of-duties control on payment instructions | Listed as to-be-built in 4.4.3; depends on the banking channel entitlements in Section 3.3 item E1 | Edward | Before go-live |
| 5 | Whether the third-party verification provider processes identity or biometric data outside Vietnam | Determines whether a transfer impact assessment is required for biometric data and whether the provider must be replaced or relocated to meet 4.4.6. **The most material open item in this section** | Edward, with counsel | 2026-08-14 |
| 6 | Reciprocal incident notification with VPBank, and the contact route for it | FundLok has a 72-hour clock that starts at detection, not at the point it hears about an incident on the bank side | Edward, with VPBank | Pending VPBank confirmation |
| 7 | Whether the small-business exemption from impact assessments applies to FundLok | FundLok's stated intention is not to rely on it; confirmation lets that position be stated as a choice rather than an assumption | Edward, with counsel | 2026-08-14 |
| 8 | Whether VPBank requires a data processing agreement, and on whose template | Determines the contractual layer over the exchange specified in Section 1.5 | Edward, with VPBank | Pending VPBank confirmation |
| 9 | Implementing regulations under Law 91/2025 for financial and credit activities | The law's sector-specific safeguards await implementing detail; this section may need revision when it is published | Edward, with counsel | Ongoing |
| 10 | Whether the T-VAN interface can supply aggregate daily revenue without invoice-level counterparty detail | Determines whether FundLok processes personal data of the borrower's own customers at all | Edward, with counsel | Before the integration is built |
| 11 | Lawful basis and consent wording for the T-VAN sales feed, including the borrower's authority to permit it | The borrower consents to FundLok reading its sales data; whether that consent extends to data about the borrower's own customers is a distinct question | Edward, with counsel | 2026-08-14 |

---

*Dependencies: none. Consistent with Section 1.4 (money flow, and the T-VAN sales feed it depends on), Section 1.5 (data flow), Section 3.3 (channel security requirements), Section 3.5 (FundLok's build) and Section 3.7 (go-live staging). Insolvency treatment and the accounting position of escrow balances are documented in Section 4.5.*
