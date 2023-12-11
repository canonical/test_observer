"""Add test execution review status and comment

Revision ID: f7b452b19e46
Revises: b8e8c3053273
Create Date: 2023-12-11 08:02:27.583110+00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "f7b452b19e46"
down_revision = "b8e8c3053273"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE testexecutionreviewstatus AS "
        "ENUM( "
        "'REJECTED', "
        "'APPROVED_INCONSISTENT_TEST', "
        "'APPROVED_UNSTABLE_PHYSICAL_INFRA', "
        "'APPROVED_FAULTY_HARDWARE', "
        "'APPROVED_ALL_TESTS_PASS' "
        ")"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_status testexecutionreviewstatus[] NOT NULL "
        "DEFAULT '{}'::testexecutionreviewstatus[]"
    )
    op.add_column(
        "test_execution",
        sa.Column("review_comment", sa.String(), nullable=False, default=""),
    )


def downgrade() -> None:
    op.drop_column("test_execution", "review_comment")
    op.drop_column("test_execution", "review_status")
    op.execute("DROP TYPE testexecutionreviewstatus")
