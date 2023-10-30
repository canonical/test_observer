"""Add track, store, series, repo to Artefact

Revision ID: cb121ad343dd
Revises: ce0b50f657e9
Create Date: 2023-10-25 11:39:46.208427+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "cb121ad343dd"
down_revision = "ce0b50f657e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("track", sa.String(), nullable=True))
    op.add_column("artefact", sa.Column("store", sa.String(), nullable=True))
    op.add_column("artefact", sa.Column("series", sa.String(), nullable=True))
    op.add_column("artefact", sa.Column("repo", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("artefact", "repo")
    op.drop_column("artefact", "series")
    op.drop_column("artefact", "store")
    op.drop_column("artefact", "track")
