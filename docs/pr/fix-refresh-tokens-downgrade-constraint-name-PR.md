# PR: Fix broken downgrade() in 5ed837b145f0 (refresh_tokens unique constraint)

**Branch:** `fix/refresh-tokens-downgrade-constraint-name` (off `main` @ `ed6df8e`)
**Found in:** [feature/ledger/double-entry-foundation PR](./ledger-double-entry-foundation-PR.md)

## The bug

`alembic/versions/5ed837b145f0_add_full_name_to_users.py`:

- `upgrade()` calls `op.create_unique_constraint(None, 'refresh_tokens', ['token_hash'])`. Passing `None` here is fine — Postgres auto-names it using its default convention: `refresh_tokens_token_hash_key`.
- `downgrade()` then calls `op.drop_constraint(None, 'refresh_tokens', type_='unique')`. `None` cannot compile into `DROP CONSTRAINT` — unlike `CREATE`, `DROP` needs a real name. This raised `CompileError: Can't emit DROP CONSTRAINT for constraint UniqueConstraint(); it has no name`.

Net effect: a full `alembic downgrade base` failed every time, at this exact step, regardless of what else was in the chain.

## The fix

One line: `downgrade()` now calls `op.drop_constraint('refresh_tokens_token_hash_key', 'refresh_tokens', type_='unique')` — the actual name Postgres already gives that constraint. `upgrade()` is untouched, so the schema this migration produces is byte-for-byte identical to before; only the downgrade path changes.

## Why editing an already-merged migration is safe here

CLAUDE.md's migration history freeze exists to prevent schema drift between environments that already ran a migration's `upgrade()` and a fresh environment that would run an edited version. That risk doesn't apply here: `upgrade()` isn't touched, and `downgrade()` never successfully executed before this fix — it raised a `CompileError` on every attempt, in every environment, always. There is no environment anywhere that has ever depended on this code's prior behavior, because it had no prior successful behavior. This was confirmed with the user before making the change.

## Verification

- `alembic upgrade head` → `alembic check` → `alembic downgrade base` → `alembic upgrade head` → `alembic check`: all clean (the middle step is the one that used to fail).
- New regression test: `tests/alembic/test_migration_full_downgrade.py::test_migration_full_downgrade_to_base_and_back_up_is_clean`, run against its own throwaway database.
- Full suite: **58 passed**, 0 failed (57 pre-existing + the 1 new test).

## Files

- `alembic/versions/5ed837b145f0_add_full_name_to_users.py` — one-line fix + comment explaining the rationale in place.
- `tests/alembic/__init__.py`, `tests/alembic/test_migration_full_downgrade.py` — regression test.
