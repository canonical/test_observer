"""Fix artefact uniqueness constraint to exclude store

Revision ID: d646a347472e
Revises: 16043e3ffdd9
Create Date: 2023-10-25 13:45:11.298029+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "d646a347472e"
down_revision = "16043e3ffdd9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("unique_artefact", "artefact")
    op.create_unique_constraint(
        "unique_snap",
        "artefact",
        ["name", "version", "track"],
    )
    op.create_unique_constraint(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
    )


def downgrade() -> None:
    op.drop_constraint("unique_snap", "artefact")
    op.drop_constraint("unique_deb", "artefact")
    op.create_unique_constraint(
        "unique_artefact",
        "artefact",
        ["name", "version", "source"],
    )
