"""add case name to TestCaseIssues

Revision ID: 6f3eeb521421
Revises: c163a3149a9d
Create Date: 2024-08-30 11:59:46.965863+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6f3eeb521421"
down_revision = "c163a3149a9d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_case_issue", sa.Column("case_name", sa.String(), nullable=False)
    )
    op.create_index(
        op.f("test_case_issue_case_name_ix"),
        "test_case_issue",
        ["case_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_case_issue_case_name_ix"), table_name="test_case_issue")
    op.drop_column("test_case_issue", "case_name")
