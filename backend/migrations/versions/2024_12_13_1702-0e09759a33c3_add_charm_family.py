"""Add charm family

Revision ID: 0e09759a33c3
Revises: 4c2e5946358c
Create Date: 2024-12-13 17:02:14.136283+00:00

"""
from alembic import op
import sqlalchemy as sa

from test_observer.data_access.models_enums import FamilyName

new_families = {
    FamilyName.CHARM: ["edge", "beta", "candidate", "stable"],
}


# revision identifiers, used by Alembic.
revision = "0e09759a33c3"
down_revision = "4c2e5946358c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    family_table = sa.table(
        "family",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    stage_table = sa.table(
        "stage",
        sa.column("name", sa.String()),
        sa.column("family_id", sa.Integer()),
        sa.column("position", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    for family_name, stage_names in new_families.items():
        # Create family
        (inserted_family,) = conn.execute(
            sa.insert(family_table)
            .values(
                name=family_name,
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
            .returning(family_table.c.id)
        )

        # Add stages
        stage_position = 10
        for stage_name in stage_names:
            conn.execute(
                sa.insert(stage_table).values(
                    name=stage_name,
                    family_id=inserted_family.id,
                    position=stage_position,
                    created_at=sa.func.now(),
                    updated_at=sa.func.now(),
                )
            )
            stage_position += 10


def downgrade() -> None:
    conn = op.get_bind()

    family_table = sa.table(
        "family",
        sa.column("id", sa.Integer()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    # Delete each family, stage deletes on cascade
    for family_name in new_families:
        conn.execute(sa.delete(family_table).where(family_table.c.name == family_name))
