"""Autodetected migration

Revision ID: 451ec6d4c102
Revises: 158244992900
Create Date: 2023-08-08 09:44:18.626976+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "451ec6d4c102"
down_revision = "158244992900"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "artefact_build_artefact_id_architecture_revision_key",
        "artefact_build",
        type_="unique",
    )
    op.drop_index("unique_artefact_build_null_revision", table_name="artefact_build")
    op.create_unique_constraint(
        "unique_artefact_build",
        "artefact_build",
        ["artefact_id", "architecture", "revision"],
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_constraint("unique_artefact_build", "artefact_build", type_="unique")
    op.create_index(
        "unique_artefact_build_null_revision",
        "artefact_build",
        ["artefact_id", "architecture"],
        unique=False,
    )
    op.create_unique_constraint(
        "artefact_build_artefact_id_architecture_revision_key",
        "artefact_build",
        ["artefact_id", "architecture", "revision"],
    )
    # ### end Alembic commands ###
