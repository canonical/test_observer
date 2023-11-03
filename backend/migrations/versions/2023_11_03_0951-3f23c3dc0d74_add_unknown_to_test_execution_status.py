"""Add unknown to test execution status

Revision ID: 3f23c3dc0d74
Revises: 49221114815a
Create Date: 2023-11-03 09:51:27.683542+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3f23c3dc0d74"
down_revision = "49221114815a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE test_status_enum ADD VALUE 'UNKNOWN'")


def downgrade() -> None:
    """This is not reversible, any UNKNOWN status will be converted to NOT_TESTED."""
    conn = op.get_bind()

    change_existing_unknowns = sa.text(
        "UPDATE test_execution SET status = 'NOT_STARTED' WHERE status = 'UNKNOWN'"
    )
    conn.execute(change_existing_unknowns)

    rename_status_enum = sa.text(
        "ALTER TYPE test_status_enum RENAME TO test_status_enum_old"
    )
    conn.execute(rename_status_enum)

    create_new_status_enum = sa.text(
        "CREATE TYPE test_status_enum AS ENUM"
        "('APPROVED', 'NOT_STARTED', 'IN_PROGRESS', 'PASSED', 'FAILED', 'NOT_TESTED')"
    )
    conn.execute(create_new_status_enum)

    switch_column_type = sa.text(
        "ALTER TABLE test_execution ALTER COLUMN status TYPE test_status_enum"
        " USING status::text::test_status_enum"
    )
    conn.execute(switch_column_type)

    drop_old_status_enum = sa.text("DROP TYPE test_status_enum_old")
    conn.execute(drop_old_status_enum)
