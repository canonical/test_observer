"""Make artefact status not nullable

Revision ID: 8317277d4333
Revises: 8d8643821588
Create Date: 2023-12-04 08:20:23.131927+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "8317277d4333"
down_revision = "8d8643821588"
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.execute("ALTER TYPE artefact_status_enum RENAME TO artefact_status_enum_old")
    op.execute(
        "CREATE TYPE artefact_status_enum AS ENUM('APPROVED', 'MARKED_AS_FAILED')"
    )
    op.execute("ALTER TABLE artefact ALTER COLUMN status SET NULL")
    op.execute("UPDATE artefact SET status = NULL WHERE status = 'UNDECIDED'")
    op.execute(
        "ALTER TABLE artefact ALTER COLUMN status TYPE "
        "artefact_status_enum USING status::text::artefact_status_enum"
    )
    op.execute("DROP TYPE artefact_status_enum_old")
