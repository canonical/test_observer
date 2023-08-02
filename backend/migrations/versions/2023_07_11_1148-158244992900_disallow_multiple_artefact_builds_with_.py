"""disallow multiple artefact builds with null revision

Revision ID: 158244992900
Revises: b33ee8dd41b1
Create Date: 2023-07-11 11:48:49.777726+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "158244992900"
down_revision = "6a80dad01d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "unique_artefact_build_null_revision",
        "artefact_build",
        ["artefact_id", "architecture"],
        unique=True,
        postgresql_where=("revision IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "unique_artefact_build_null_revision",
        "artefact_build",
    )
