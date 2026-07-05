"""Add ledger_entries.idempotency_key (align DB with ORM).

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("ledger_entries", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.create_unique_constraint(
        "uq_ledger_entries_idempotency_key",
        "ledger_entries",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_ledger_entries_idempotency_key", "ledger_entries", type_="unique")
    op.drop_column("ledger_entries", "idempotency_key")
