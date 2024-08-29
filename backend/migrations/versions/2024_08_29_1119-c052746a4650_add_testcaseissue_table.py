"""add TestCaseIssue table

Revision ID: c052746a4650
Revises: 2745d4e5bc72
Create Date: 2024-08-29 11:19:00.502332+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c052746a4650"
down_revision = "2745d4e5bc72"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_case_issue",
        sa.Column("template_id", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("test_case_issue_pkey")),
    )


def downgrade() -> None:
    op.drop_table("test_case_issue")
