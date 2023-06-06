"""Use python Enum in data model

Revision ID: 6a80dad01d24
Revises: b2c80c6f87c1
Create Date: 2023-06-01 07:28:40.295778+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6a80dad01d24"
down_revision = "b2c80c6f87c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE artefact_status_enum RENAME VALUE 'Approved' TO 'APPROVED'")
    op.execute(
        "ALTER TYPE artefact_status_enum RENAME VALUE 'Marked as Failed' TO 'MARKED_AS_FAILED'"
    )

    op.execute(
        "ALTER TYPE test_status_enum RENAME VALUE 'Not Started' TO 'NOT_STARTED'"
    )
    op.execute(
        "ALTER TYPE test_status_enum RENAME VALUE 'In Progress' TO 'IN_PROGRESS'"
    )
    op.execute("ALTER TYPE test_status_enum RENAME VALUE 'Passed' TO 'PASSED'")
    op.execute("ALTER TYPE test_status_enum RENAME VALUE 'Failed' TO 'FAILED'")
    op.execute("ALTER TYPE test_status_enum RENAME VALUE 'Not Tested' TO 'NOT_TESTED'")


def downgrade() -> None:
    op.execute("ALTER TYPE artefact_status_enum RENAME VALUE 'APPROVED' TO 'Approved'")
    op.execute(
        "ALTER TYPE artefact_status_enum RENAME VALUE 'MARKED_AS_FAILED' TO 'Marked as Failed'"
    )

    op.execute(
        "ALTER TYPE test_status_enum RENAME VALUE 'NOT_STARTED' TO 'Not Started'"
    )
    op.execute(
        "ALTER TYPE test_status_enum RENAME VALUE 'IN_PROGRESS' TO 'In Progress'"
    )
    op.execute("ALTER TYPE test_status_enum RENAME VALUE 'PASSED' TO 'Passed'")
    op.execute("ALTER TYPE test_status_enum RENAME VALUE 'FAILED' TO 'Failed'")
    op.execute("ALTER TYPE test_status_enum RENAME VALUE 'NOT_TESTED' TO 'Not Tested'")
