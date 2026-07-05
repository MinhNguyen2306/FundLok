"""Add orders.idempotency_key (align DB with ORM).

Revision ID: 0002
Revises: a7c4f1e2d3b5
Create Date: 2026-03-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "a7c4f1e2d3b5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("idempotency_key", sa.Text(), nullable=True))
    op.create_unique_constraint("uq_orders_idempotency_key", "orders", ["idempotency_key"])


def downgrade() -> None:
    op.drop_constraint("uq_orders_idempotency_key", "orders", type_="unique")
    op.drop_column("orders", "idempotency_key")
