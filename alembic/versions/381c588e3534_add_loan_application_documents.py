"""add_loan_application_documents

Revision ID: 381c588e3534
Revises: d867097c063a
Create Date: 2026-06-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "381c588e3534"
down_revision: Union[str, None] = "d867097c063a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loan_application_documents",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("loan_application_id", UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("file_key", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("status", sa.Text(), server_default="PENDING", nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=True),
        sa.CheckConstraint(
            "document_type IN ('legal_charter', 'business_registration', 'vat_tax_zip', "
            "'financial_report', 'e_invoice_data', 'cic_report')",
            name="loan_application_documents_document_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'UPLOADED')",
            name="loan_application_documents_status_check",
        ),
        sa.ForeignKeyConstraint(["loan_application_id"], ["loan_applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_key"),
    )
    op.create_index(
        "ix_loan_application_documents_app_doc_type",
        "loan_application_documents",
        ["loan_application_id", "document_type"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_loan_application_documents_app_doc_type", table_name="loan_application_documents")
    op.drop_table("loan_application_documents")
