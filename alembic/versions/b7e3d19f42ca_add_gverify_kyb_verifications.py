"""add gverify_kyb_verifications table (GVerify eKYB business verification)

Revision ID: b7e3d19f42ca
Revises: 4c8ed05b93a1
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b7e3d19f42ca'
down_revision: Union[str, None] = '4c8ed05b93a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('gverify_kyb_verifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('status', sa.Text(), server_default='PENDING', nullable=False),
    sa.Column('document_type', sa.Text(), nullable=False),
    sa.Column('ocr_transaction_code', sa.Text(), nullable=True),
    sa.Column('tax_transaction_code', sa.Text(), nullable=True),
    sa.Column('tax_code', sa.Text(), nullable=True),
    sa.Column('business_name', sa.Text(), nullable=True),
    sa.Column('business_type', sa.Text(), nullable=True),
    sa.Column('company_address', sa.Text(), nullable=True),
    sa.Column('date_of_establishment', sa.Text(), nullable=True),
    sa.Column('charter_capital', sa.Text(), nullable=True),
    sa.Column('representatives', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ocr_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('tax_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rejection_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gverify_kyb_verifications_user_id'), 'gverify_kyb_verifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_gverify_kyb_verifications_tax_code'), 'gverify_kyb_verifications', ['tax_code'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_gverify_kyb_verifications_tax_code'), table_name='gverify_kyb_verifications')
    op.drop_index(op.f('ix_gverify_kyb_verifications_user_id'), table_name='gverify_kyb_verifications')
    op.drop_table('gverify_kyb_verifications')
