"""merge HANDOFF-03 ledger/scoring chain with main's auth/lite-grading chain

Revision ID: 7bbdda89ceba
Revises: b7d2e4a9c150, 298cd240e4f1
Create Date: 2026-09-17 16:41:53.123693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bbdda89ceba'
down_revision: Union[str, None] = ('b7d2e4a9c150', '298cd240e4f1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
