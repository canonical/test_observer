"""Merge success and failed TE status to completed

Revision ID: 94125a714b27
Revises: 4c2e5946358c
Create Date: 2024-12-10 12:18:00.831155+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "94125a714b27"
down_revision = "4c2e5946358c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE test_execution ALTER COLUMN status DROP NOT NULL")
    op.execute(
        "UPDATE test_execution SET status = NULL "
        "WHERE status IN ('PASSED', 'FAILED')"
    )
    op.execute(
        "UPDATE test_execution SET status = 'NOT_STARTED' "
        "WHERE status = 'NOT_TESTED'"
    )

    op.execute("ALTER TYPE testexecutionstatus RENAME TO testexecutionstatus_old")
    op.execute(
        "CREATE TYPE testexecutionstatus"
        " AS ENUM('NOT_STARTED', 'IN_PROGRESS', 'ENDED_PREMATURELY', 'COMPLETED')"
    )

    op.execute(
        "ALTER TABLE test_execution ALTER COLUMN status TYPE"
        " testexecutionstatus USING status::text::testexecutionstatus"
    )
    op.execute("UPDATE test_execution SET status = 'COMPLETED' WHERE status is NULL")
    op.execute("ALTER TABLE test_execution ALTER COLUMN status SET NOT NULL")
    op.execute("DROP TYPE testexecutionstatus_old")


set_proper_status = """
UPDATE test_execution te
SET status =
    CASE
        WHEN (
            SELECT COUNT(*) 
            FROM test_result tr
            WHERE tr.test_execution_id = te.id AND tr.status = 'FAILED'
        ) > 0 THEN 'FAILED'::testexecutionstatus
        WHEN (
            SELECT COUNT(*) 
            FROM test_result tr
            WHERE tr.test_execution_id = te.id
        ) > 0 THEN 'PASSED'::testexecutionstatus
        ELSE 'IN_PROGRESS'::testexecutionstatus
    END
WHERE status is NULL
"""


def downgrade() -> None:
    op.execute("ALTER TABLE test_execution ALTER COLUMN status DROP NOT NULL")
    op.execute("UPDATE test_execution SET status = NULL WHERE status = 'COMPLETED'")

    op.execute("ALTER TYPE testexecutionstatus RENAME TO testexecutionstatus_old")
    op.execute(
        "CREATE TYPE testexecutionstatus"
        " AS ENUM('NOT_STARTED', 'IN_PROGRESS', 'ENDED_PREMATURELY', "
        "'PASSED', 'FAILED', 'NOT_TESTED')"
    )

    op.execute(
        "ALTER TABLE test_execution ALTER COLUMN status TYPE"
        " testexecutionstatus USING status::text::testexecutionstatus"
    )
    op.execute(set_proper_status)
    op.execute("ALTER TABLE test_execution ALTER COLUMN status SET NOT NULL")
    op.execute("DROP TYPE testexecutionstatus_old")
