"""add gverify_verifications table (GVerify/Datatrust eKYC)

Revision ID: 4c8ed05b93a1
Revises: 6f3a29bbd701
Create Date: 2026-07-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4c8ed05b93a1'
down_revision: Union[str, None] = '6f3a29bbd701'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('gverify_verifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('verification_type', sa.Text(), server_default='KYC', nullable=False),
    sa.Column('status', sa.Text(), server_default='PENDING', nullable=False),
    sa.Column('ocr_transaction_code', sa.Text(), nullable=True),
    sa.Column('face_transaction_code', sa.Text(), nullable=True),
    sa.Column('person_number', sa.Text(), nullable=True),
    sa.Column('full_name', sa.Text(), nullable=True),
    sa.Column('date_of_birth', sa.Text(), nullable=True),
    sa.Column('ocr_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('face_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('rejection_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gverify_verifications_user_id'), 'gverify_verifications', ['user_id'], unique=False)
    op.create_index(op.f('ix_gverify_verifications_verification_type'), 'gverify_verifications', ['verification_type'], unique=False)
    op.create_index(op.f('ix_gverify_verifications_person_number'), 'gverify_verifications', ['person_number'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_gverify_verifications_person_number'), table_name='gverify_verifications')
    op.drop_index(op.f('ix_gverify_verifications_verification_type'), table_name='gverify_verifications')
    op.drop_index(op.f('ix_gverify_verifications_user_id'), table_name='gverify_verifications')
    op.drop_table('gverify_verifications')
