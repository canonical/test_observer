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
    _add_source_column()
    _change_unique_constraints()


def downgrade() -> None:
    op.execute("DELETE FROM artefact WHERE source != ''")
    _revert_unique_constraints()
    op.drop_column("artefact", "source")


def _add_source_column() -> None:
    op.add_column("artefact", sa.Column("source", sa.String(length=200)))
    op.execute("UPDATE artefact SET source = '' WHERE source is NULL")
    op.alter_column("artefact", "source", nullable=False)


def _change_unique_constraints() -> None:
    op.drop_index("unique_deb", "artefact")

    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo", "source"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )


def _revert_unique_constraints() -> None:
    op.drop_index("unique_deb", "artefact")

    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
        unique=True,
        postgresql_where=sa.text("family = 'deb'"),
    )
