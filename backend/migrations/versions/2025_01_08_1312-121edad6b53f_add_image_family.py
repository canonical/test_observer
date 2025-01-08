"""Add image family

Revision ID: 121edad6b53f
Revises: 7878a1b29384
Create Date: 2025-01-08 13:12:05.831020+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "121edad6b53f"
down_revision = "7878a1b29384"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE familyname ADD VALUE IF NOT EXISTS 'image'")
    op.execute("ALTER TYPE stagename ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE stagename ADD VALUE IF NOT EXISTS 'current'")


def downgrade() -> None:
    # Downgrading could be an issue if the new values were used
    # so it's likely better to avoid doing anything in this case
    pass
