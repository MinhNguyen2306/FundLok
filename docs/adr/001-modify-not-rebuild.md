# ADR-001: Modify MVP Codebase, Do Not Rebuild

| Field | Value |
|---|---|
| **Status** | Accepted |
| **Date** | June 2026 |
| **Deciders** | Edward Wong (CTO) |

## Context

FundLok has an existing MVP backend (FastAPI + PostgreSQL). V2 requirements include Vietnam Banking Open API integration (Brankas), Vietnam Decree 94/2025/ND-CP compliance, a real ML grading engine, repayment schedules, and share conversion. The team evaluated whether to rebuild from scratch or extend the MVP.

## Decision

Extend (modify) the existing codebase. Do not rebuild.

## Rationale

The MVP's core domain model, lending state machine, idempotency pattern, and infrastructure are production-quality. V2 requirements are predominantly additive — new modules alongside existing ones, not replacements of them. A rebuild would cost 6–8 weeks re-deriving correct logic for a 2-engineer team. The modify path delivers V2 features in approximately half that time.

Four structural issues must be resolved before V2 feature work begins (Phase 0):
1. Migrate DB layer to async (asyncpg + SQLAlchemy AsyncSession)
2. Restore DB-backed refresh token revocation (currently stateless JWTs)
3. Write test suite covering core workflow
4. Consolidate module structure (merge app/files/ into app/uploads/)

Full analysis: `docs/FundLok_V2_Rebuild_vs_Modify_v1.1.docx`

## Consequences

- Existing 5 Alembic migrations are frozen. Never alter them.
- All V2 schema changes via new migrations only.
- The async migration (Phase 0) changes `app/core/database.py` and all service files — this is a breaking change reviewed as a single PR.
