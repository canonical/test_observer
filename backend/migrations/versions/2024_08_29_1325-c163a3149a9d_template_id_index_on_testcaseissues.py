"""template_id index on TestCaseIssues

Revision ID: c163a3149a9d
Revises: c052746a4650
Create Date: 2024-08-29 13:25:21.856165+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "c163a3149a9d"
down_revision = "c052746a4650"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        op.f("test_case_issue_template_id_ix"),
        "test_case_issue",
        ["template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_case_issue_template_id_ix"), table_name="test_case_issue")
