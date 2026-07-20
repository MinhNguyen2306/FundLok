"""add license_code to gverify_kyb_verifications

Revision ID: c9f2a71b83e4
Revises: b7e3d19f42ca
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9f2a71b83e4'
down_revision: Union[str, None] = 'b7e3d19f42ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'gverify_kyb_verifications',
        sa.Column('license_code', sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('gverify_kyb_verifications', 'license_code')
