"""Add test execution review status and comment

Revision ID: e39a45a38d1f
Revises: 871eec26dc90
Create Date: 2023-12-07 14:51:57.662163+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e39a45a38d1f"
down_revision = "871eec26dc90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE testexecutionreviewstatus AS "
        "ENUM( "
        "'UNDECIDED', "
        "'MARKED_AS_FAILED', "
        "'APPROVED_INCONSISTENT_TEST_DEF', "
        "'APPROVED_UNSTABLE_PHSYICAL_INFRA', "
        "'APPROVED_FAULTY_HARDWARE', "
        "'APPROVED_GENERIC' "
        ")"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_status testexecutionreviewstatus[] "
        "DEFAULT '{UNDECIDED}'::testexecutionreviewstatus[]"
    )
    op.add_column(
        "test_execution", sa.Column("review_comment", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("test_execution", "review_comment")
    op.drop_column("test_execution", "review_status")
    op.execute("DROP TYPE testexecutionreviewstatus")
