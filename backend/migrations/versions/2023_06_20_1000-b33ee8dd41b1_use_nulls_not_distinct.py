"""Use nulls not distinct

Revision ID: b33ee8dd41b1
Revises: 6a80dad01d24
Create Date: 2023-06-20 10:00:07.676129+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "b33ee8dd41b1"
down_revision = "6a80dad01d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE artefact_build "
        "DROP CONSTRAINT IF EXISTS artefact_build_artefact_id_architecture_revision_key"
        ", ADD CONSTRAINT unique_artefact_build "
        "UNIQUE NULLS NOT DISTINCT (artefact_id, architecture, revision);"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE artefact_build "
        "DROP CONSTRAINT IF EXISTS unique_artefact_build"
        ", ADD CONSTRAINT artefact_build_artefact_id_architecture_revision_key "
        "UNIQUE (artefact_id, architecture, revision);"
    )
