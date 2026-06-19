"""add avatar_key to users

Revision ID: c4d1e9f0a7b2
Revises: 381c588e3534
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c4d1e9f0a7b2"
down_revision: Union[str, None] = "381c588e3534"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_key", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_key")
