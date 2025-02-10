"""Add archival option to artefact status

Revision ID: ffe7537037a9
Revises: 2be627e68efd
Create Date: 2025-02-10 20:56:43.320141+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffe7537037a9'
down_revision = '2be627e68efd'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("ALTER TYPE artefact_status_enum RENAME TO artefact_status_enum_old")
    op.execute(
        "CREATE TYPE artefact_status_enum AS "
        "ENUM('APPROVED', 'MARKED_AS_FAILED', 'UNDECIDED', 'ARCHIVED')"
    )
    op.execute(
        "ALTER TABLE artefact ALTER COLUMN status TYPE "
        "artefact_status_enum USING status::text::artefact_status_enum"
    )
    op.execute("DROP TYPE artefact_status_enum_old")
    op.execute("UPDATE artefact SET status = 'UNDECIDED' WHERE status IS NULL")
    op.execute("ALTER TABLE artefact ALTER COLUMN status SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TYPE artefact_status_enum RENAME TO artefact_status_enum_old")
    op.execute(
        "CREATE TYPE artefact_status_enum AS "
        "ENUM('APPROVED', 'MARKED_AS_FAILED', 'UNDECIDED')"
    )
    op.execute(
        "ALTER TABLE artefact ALTER COLUMN status TYPE "
        "artefact_status_enum USING status::text::artefact_status_enum"
    )
    op.execute("DROP TYPE artefact_status_enum_old")
    op.execute("UPDATE artefact SET status = 'UNDECIDED' WHERE status IS NULL")
    op.execute("ALTER TABLE artefact ALTER COLUMN status SET NOT NULL")
