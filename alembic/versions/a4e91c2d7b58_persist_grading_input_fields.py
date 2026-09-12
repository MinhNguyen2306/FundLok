"""persist the grading inputs the form already collects

Adds the three values `docs/specs/underwriting/grading-input-sources.md` §3.3
records as collected, validated and then discarded:

    projects.employee_count   -- headcount as entered by the SME
    projects.company_size     -- derived from it server-side (§6.3)
    loan_applications.duration_months -- loan term

`build_grading_input()` takes `employee_count` and `duration_months` as
non-optional arguments, so until these columns exist no caller can assemble a
`GradingInput` from a stored application at all -- which is why `grade_lite()`
had no callers.

All three are nullable: existing rows predate the columns, and a project
created before this migration genuinely has no headcount on file. A
not-null default would invent one and silently mis-size every historic
applicant.

`company_size` carries a CHECK rather than a Postgres ENUM: the bands come from
`grading_params_v1.yaml`, and a params change that renamed a band would need a
type migration instead of a constraint edit.

Revision ID: a4e91c2d7b58
Revises: c31a7de904f6
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4e91c2d7b58'
down_revision: Union[str, None] = 'c31a7de904f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'projects',
        sa.Column('employee_count', sa.Integer(), nullable=True),
    )
    op.add_column(
        'projects',
        sa.Column('company_size', sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        'ck_projects_company_size',
        'projects',
        "company_size IS NULL OR company_size IN ('micro', 'small', 'medium')",
    )
    op.add_column(
        'loan_applications',
        sa.Column('duration_months', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('loan_applications', 'duration_months')
    op.drop_constraint('ck_projects_company_size', 'projects', type_='check')
    op.drop_column('projects', 'company_size')
    op.drop_column('projects', 'employee_count')
