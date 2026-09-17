"""add security preferences to users

Sign-in alerts: email the account owner when a device that has not been seen
before signs in. Off by default -- an existing user did not ask for the mail,
and turning it on for everybody retroactively is a surprise, not a feature.

Revision ID: b8d41c60ea92
Revises: a3f7c92e1b48
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b8d41c60ea92'
down_revision: Union[str, None] = 'a3f7c92e1b48'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'signin_alerts_enabled',
            sa.Boolean(),
            nullable=False,
            server_default='false',
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'signin_alerts_enabled')
