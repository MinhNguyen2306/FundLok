# Spec: [Feature Name]

<!-- 
  INSTRUCTIONS (delete this block before merging)
  
  - One spec per feature. A "feature" is a unit of work one engineer can own end-to-end.
  - The spec is complete when the other engineer can implement against it with zero verbal clarification.
  - Specs are reviewed via PR before any implementation begins.
  - Acceptance criteria become test function names — write them testably.
  - Owner field = the engineer who writes AND is accountable for the spec (not necessarily the implementer).
-->

| Field | Value |
|---|---|
| **Status** | DRAFT \| REVIEW \| ACCEPTED \| IMPLEMENTED |
| **Owner** | Edward \| Phat |
| **Implementer(s)** | Edward (backend) / Phat (frontend) / Both |
| **Module** | `app/<module>/` |
| **Version** | 1.0 |
| **Date** | YYYY-MM-DD |
| **Related ADR** | ADR-XXX (if applicable) |
| **Depends on** | Links to other specs this one builds on |

---

## 1. Context & Goal

<!-- 
  2–4 sentences. Why does this feature exist? What problem does it solve for the user or the platform?
  Include the regulatory or business driver if relevant.
-->

**Goal:** [One sentence — what this spec delivers]

---

## 2. Out of Scope

<!-- 
  Explicitly list what this spec does NOT cover. This is as important as what it does cover.
  Prevents scope creep and clarifies what a future spec must handle.
-->

- ...
- ...

---

## 3. Data Model

<!--
  Define every new table, column, or schema change.
  Use typed pseudocode — not prose. Be explicit about nullability, enums, and constraints.
  Schema changes are implemented as Alembic migrations only — reference the migration number once known.
-->

### New Table: `table_name`

```
table_name
├── id                UUID          PK, default gen_random_uuid()
├── foreign_id        UUID          NOT NULL → references other_table(id) ON DELETE CASCADE
├── status            TEXT          NOT NULL, CHECK IN ('STATE_A', 'STATE_B', 'STATE_C')
├── amount            DECIMAL(15,2) NOT NULL
├── metadata          JSONB         nullable
├── created_at        TIMESTAMPTZ   DEFAULT NOW()
└── updated_at        TIMESTAMPTZ   DEFAULT NOW()
```

### Modified Table: `existing_table` (if applicable)

```
+ new_column   TEXT   nullable   -- reason for addition
```

### Alembic Migration

`alembic/versions/XXXX_<description>.py` (number assigned at implementation time)

---

## 4. API Contract

<!--
  Define every endpoint this feature adds or modifies.
  Both sides (backend author, frontend consumer) agree on this before either writes code.
  Types must be explicit — no "object" or "any".
-->

### `POST /module/endpoint`

**Auth:** Bearer JWT — roles: `ADMIN` | `SME` | `INVESTOR` | public

**Request**
```json
{
  "field_name": "string",         // required — description
  "amount": "decimal string",     // required — e.g. "1000.00"
  "optional_field": "string|null" // optional
}
```

**Headers**
```
Idempotency-Key: <uuid>   // required for any financial write
```

**Response 201**
```json
{
  "id": "uuid",
  "status": "STATE_A",
  "created_at": "2026-06-01T00:00:00Z"
}
```

**Error Responses**

| Status | Code | Condition |
|---|---|---|
| 400 | `INVALID_AMOUNT` | amount ≤ 0 |
| 404 | `NOT_FOUND` | referenced resource does not exist |
| 409 | `IDEMPOTENCY_CONFLICT` | Idempotency-Key used for a different resource |
| 422 | — | Pydantic validation failure |

---

## 5. State Machine

<!--
  Include only if this feature introduces or modifies a status field.
  Diagram the valid transitions. Be explicit about what triggers each transition and who can trigger it.
-->

```
STATE_A  ──[trigger: action by ROLE]──►  STATE_B
STATE_B  ──[trigger: action by ROLE]──►  STATE_C
STATE_B  ──[trigger: condition]────────►  STATE_A  (rollback case)
```

**Transition rules:**
- `STATE_A → STATE_B`: triggered by X, only by role Y, requires condition Z
- `STATE_B → STATE_C`: triggered by Brankas webhook `SETTLED`
- Invalid transitions must return 400 with message `"Invalid state transition: {current} → {target}"`

---

## 6. Business Rules

<!--
  Numbered list. Each rule must be unambiguous and testable.
  If a rule comes from Decree 94 or another regulatory requirement, cite it.
-->

1. ...
2. ...
3. ...

---

## 7. Error Cases

<!--
  Walk through every failure scenario the implementation must handle.
  Include: what went wrong, what the system does, what the user/caller sees.
-->

| Scenario | System behaviour | Response to caller |
|---|---|---|
| Brankas webhook arrives twice (same transaction_id) | Idempotency check returns existing record, no duplicate write | 200 with existing record |
| Brankas reports FAILED on outbound payment | Set bank_transaction.status = FAILED, emit audit log, alert ops | — (async, no caller) |
| ... | ... | ... |

---

## 8. Acceptance Criteria

<!--
  These become pytest function names. Write them as "given/when/then" or "it should" statements.
  Every criterion must be binary — pass or fail, no ambiguity.
-->

- [ ] `test_<feature>_happy_path` — given valid input, returns 201 with correct response shape
- [ ] `test_<feature>_idempotency` — given same Idempotency-Key, second call returns existing record, no duplicate DB row
- [ ] `test_<feature>_rejects_invalid_state` — given resource in wrong state, returns 400
- [ ] `test_<feature>_rejects_unauthorized_role` — given wrong role, returns 403
- [ ] `test_<feature>_not_found` — given non-existent resource ID, returns 404
- [ ] [add feature-specific criteria]

---

## 9. Open Questions

<!--
  Unresolved questions that block finalising the spec. Each must be assigned to someone.
  Close all open questions before moving spec to ACCEPTED.
-->

| # | Question | Owner | Resolution |
|---|---|---|---|
| 1 | ... | Edward / Phat | — |

---

## Changelog

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | YYYY-MM-DD | Edward / Phat | Initial draft |
