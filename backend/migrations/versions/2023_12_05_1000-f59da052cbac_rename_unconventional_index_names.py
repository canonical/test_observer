"""Rename unconventional index names

Revision ID: f59da052cbac
Revises: 808f2035f714
Create Date: 2023-12-05 10:00:21.171939+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f59da052cbac"
down_revision = "808f2035f714"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "idx_artefact_id_architecture_null_revision",
        table_name="artefact_build",
        postgresql_where="(revision IS NULL)",
    )
    op.drop_index(
        "idx_artefact_id_architecture_revision",
        table_name="artefact_build",
        postgresql_where="(revision IS NOT NULL)",
    )
    op.create_index(
        op.f("artefact_build_artefact_id_architecture_ix"),
        "artefact_build",
        ["artefact_id", "architecture"],
        unique=True,
        postgresql_where=sa.text("revision IS NULL"),
    )
    op.create_index(
        op.f("artefact_build_artefact_id_architecture_revision_ix"),
        "artefact_build",
        ["artefact_id", "architecture", "revision"],
        unique=True,
        postgresql_where=sa.text("revision IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        op.f("artefact_build_artefact_id_architecture_revision_ix"),
        table_name="artefact_build",
        postgresql_where=sa.text("revision IS NOT NULL"),
    )
    op.drop_index(
        op.f("artefact_build_artefact_id_architecture_ix"),
        table_name="artefact_build",
        postgresql_where=sa.text("revision IS NULL"),
    )
    op.create_index(
        "idx_artefact_id_architecture_revision",
        "artefact_build",
        ["artefact_id", "architecture", "revision"],
        unique=False,
        postgresql_where="(revision IS NOT NULL)",
    )
    op.create_index(
        "idx_artefact_id_architecture_null_revision",
        "artefact_build",
        ["artefact_id", "architecture"],
        unique=False,
        postgresql_where="(revision IS NULL)",
    )
