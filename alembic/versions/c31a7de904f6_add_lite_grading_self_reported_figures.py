"""add lite grading self-reported figures

Revision ID: c31a7de904f6
Revises: 4fbb3ee1e5ec
Create Date: 2026-09-06 23:58:12.104883

Adds the columns behind the Lite grading path, where the applicant types the
revenue and cost figures instead of uploading the VAT and annual-report
bundles that used to stand in for them.

Purely additive: both columns are nullable with no default, so every existing
application keeps working and reads back as "no figures stated yet".
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c31a7de904f6'
down_revision: Union[str, None] = '4fbb3ee1e5ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'loan_applications',
        # JSONB, not one column per figure: the Lite field list is still
        # provisional and this history is append-only, so typed columns would
        # cost a migration per revision. The shape is enforced by
        # LoanApplicationFiguresIn at the API boundary.
        sa.Column('self_reported_figures', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        'loan_applications',
        sa.Column('figures_updated_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('loan_applications', 'figures_updated_at')
    op.drop_column('loan_applications', 'self_reported_figures')
