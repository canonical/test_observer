"""Add artefact comment

Revision ID: 5e1ae326c8fc
Revises: b582856bd72e
Create Date: 2025-05-28 09:58:17.144197+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5e1ae326c8fc"
down_revision = "b582856bd72e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("comment", sa.String()))
    op.execute("UPDATE artefact SET comment = '' WHERE comment is NULL")
    op.alter_column("artefact", "comment", nullable=False)


def downgrade() -> None:
    op.drop_column("artefact", "comment")
