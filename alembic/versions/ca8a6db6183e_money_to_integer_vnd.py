"""Money to integer VND (T1, HANDOFF-03).

Repayment spec §14: "Money is integer VND everywhere. No sub-unit. No
decimals anywhere in the system." Every money column in the codebase was
`Numeric(15, 2)` (or `Numeric(12, 2)` for `listings.min_ticket`) -- two
decimal places of a currency (VND) that has no sub-unit at all. This widens
every money column to `Numeric(20, 0)`:

  - ledger_entries.amount
  - contracts.target_amount, contracts.funded_amount
  - listings.target_amount, listings.funded_amount, listings.min_ticket
  - orders.amount
  - holdings.principal
  - loan_applications.requested_amount

Deliberately NOT touched: `score_runs.overall_score` (Numeric(5,2), a grade
score not money -- HANDOFF-03 Issue 4 covers that separately) and
`holdings.share_ratio` (Numeric(10,8), a proportion, not money).

Any pre-existing fractional value is rounded (not truncated) to the nearest
đồng on the way in via `ROUND(...)::numeric(20,0)` -- this repo's demo data
is expected to hold only whole-VND amounts already, so this is a type
widening in practice, not a real rounding event.

Do this before any facility table exists (T6) -- retrofitting after the
ledger carries real schedule/payment data would be a data migration, not a
type change.

Spec: docs/handoffs/HANDOFF-03-mvp-backend-tasks.md, Issue 7 / T1.

Revision ID: ca8a6db6183e
Revises: d5a8c31f6b02
Create Date: 2026-09-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca8a6db6183e"
down_revision: Union[str, None] = "d5a8c31f6b02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (table, column, old_precision, old_scale) -- old values only used to
# reconstruct the exact prior type on downgrade.
MONEY_COLUMNS = [
    ("ledger_entries", "amount", 15, 2),
    ("contracts", "target_amount", 15, 2),
    ("contracts", "funded_amount", 15, 2),
    ("listings", "target_amount", 15, 2),
    ("listings", "funded_amount", 15, 2),
    ("listings", "min_ticket", 12, 2),
    ("orders", "amount", 15, 2),
    ("holdings", "principal", 15, 2),
    ("loan_applications", "requested_amount", 15, 2),
]


def upgrade() -> None:
    for table, column, _old_precision, _old_scale in MONEY_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.Numeric(20, 0),
            postgresql_using=f"ROUND({column})::numeric(20,0)",
        )


def downgrade() -> None:
    for table, column, old_precision, old_scale in MONEY_COLUMNS:
        op.alter_column(
            table,
            column,
            type_=sa.Numeric(old_precision, old_scale),
            postgresql_using=f"{column}::numeric({old_precision},{old_scale})",
        )
