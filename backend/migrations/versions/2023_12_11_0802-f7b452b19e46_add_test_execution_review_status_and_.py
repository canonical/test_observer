"""Add test execution review decision and comment

Revision ID: f7b452b19e46
Revises: b8e8c3053273
Create Date: 2023-12-11 08:02:27.583110+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f7b452b19e46"
down_revision = "b8e8c3053273"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE testexecutionreviewdecision AS "
        "ENUM( "
        "'REJECTED', "
        "'APPROVED_INCONSISTENT_TEST', "
        "'APPROVED_UNSTABLE_PHYSICAL_INFRA', "
        "'APPROVED_FAULTY_HARDWARE', "
        "'APPROVED_CUSTOMER_PREREQUISITE_FAIL', "
        "'APPROVED_ALL_TESTS_PASS' "
        ")"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_decision testexecutionreviewdecision[] NOT NULL "
        "DEFAULT '{}'::testexecutionreviewdecision[]"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_comment VARCHAR NOT NULL DEFAULT ''"
    )


def downgrade() -> None:
    op.drop_column("test_execution", "review_comment")
    op.drop_column("test_execution", "review_decision")
    op.execute("DROP TYPE testexecutionreviewdecision")
