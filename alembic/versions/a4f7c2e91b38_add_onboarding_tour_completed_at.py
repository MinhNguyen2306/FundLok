"""add users.onboarding_tour_completed_at

Records when an account finished or skipped the first-run dashboard
walkthrough. Nullable: NULL means "has not seen it", which is the correct
default for every account that already exists.

Guarded with IF NOT EXISTS / IF EXISTS. The column was added by hand to at
least one local database ahead of this migration, because that machine's
alembic history was stamped at a revision living on an unmerged branch and
`upgrade head` could not run. A plain add_column would then fail on the first
`alembic upgrade` after the history is reconciled — for a nullable, additive
column the guard costs nothing and removes that trap.

Revision ID: a4f7c2e91b38
Revises: c31a7de904f6
Create Date: 2026-09-12

"""

from alembic import op

revision = "a4f7c2e91b38"
down_revision = "c31a7de904f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users "
        "ADD COLUMN IF NOT EXISTS onboarding_tour_completed_at TIMESTAMPTZ"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE users DROP COLUMN IF EXISTS onboarding_tour_completed_at"
    )
