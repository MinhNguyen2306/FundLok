"""make users.role nullable (role chosen after registration)

Revision ID: f2b3c4d5e6f7
Revises: e1a2b3c4d5e6
Create Date: 2026-06-24 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f2b3c4d5e6f7"
down_revision: Union[str, None] = "e1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Role is no longer chosen at registration; users start without one and
    # select it later. The existing users_role_check CHECK constraint already
    # permits NULL (a CHECK only fails on FALSE), so only NOT NULL is dropped.
    op.alter_column("users", "role", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    # Backfill any NULL roles before re-imposing NOT NULL so the migration
    # doesn't fail on rows created while role selection was pending.
    op.execute("UPDATE users SET role = 'INVESTOR' WHERE role IS NULL")
    op.alter_column("users", "role", existing_type=sa.Text(), nullable=False)
