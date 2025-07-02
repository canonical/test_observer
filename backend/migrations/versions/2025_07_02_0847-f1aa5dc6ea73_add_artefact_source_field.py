"""Add artefact source field

Revision ID: f1aa5dc6ea73
Revises: 87f9e68e61a7
Create Date: 2025-07-02 08:47:22.068336+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f1aa5dc6ea73"
down_revision = "87f9e68e61a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("source", sa.String(length=200)))
    op.execute("UPDATE artefact SET source = '' WHERE source is NULL")
    op.alter_column("artefact", "source", nullable=False)


def downgrade() -> None:
    op.drop_column("artefact", "source")
