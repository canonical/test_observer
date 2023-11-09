"""Remove test execution status from model

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
    """This is irreversible test execution statuses will be deleted
    albeit they're incorrect"""
    op.drop_column("test_execution", "status")
    op.execute("DROP TYPE test_status_enum")


def downgrade() -> None:
    op.execute(
        "CREATE TYPE test_status_enum AS ENUM"
        "('APPROVED', 'NOT_STARTED', 'IN_PROGRESS', 'PASSED', 'FAILED', 'NOT_TESTED')"
    )
    op.add_column(
        "test_execution",
        sa.Column(
            "status",
            sa.Enum(
                "Not Started",
                "In Progress",
                "Passed",
                "Failed",
                "Not Tested",
                name="test_status_enum",
            ),
            nullable=False,
        ),
    )
