"""Add store key to artefact source

Revision ID: 18b1066d92c3
Revises: 451ec6d4c102
Create Date: 2023-08-08 09:46:34.620860+00:00

"""
from alembic import op
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = "18b1066d92c3"
down_revision = "451ec6d4c102"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Ensure all 'snap' artefacts have the "store" key
    artefacts = conn.execute(
        text(
            """
        SELECT a.id, a.source
        FROM artefact AS a
        JOIN stage AS s ON a.stage_id = s.id
        JOIN family AS f ON s.family_id = f.id
        WHERE f.name = 'snap'
    """
        )
    ).fetchall()

    for artefact in artefacts:
        source_data = artefact.source
        if "store" not in source_data:
            source_data["store"] = "ubuntu"
            conn.execute(
                text(
                    "UPDATE artefact SET source = :source WHERE id = :id",
                ),
                {"source": source_data, "id": artefact.id},
            )


def downgrade() -> None:
    conn = op.get_bind()
    artefacts = conn.execute(
        text(
            """
        SELECT a.id, a.source
        FROM artefact AS a
        JOIN stage AS s ON a.stage_id = s.id
        JOIN family AS f ON s.family_id = f.id
        WHERE f.name = 'snap'
    """
        )
    ).fetchall()

    for artefact in artefacts:
        source_data = artefact.source
        if source_data.get("store", "") == "ubuntu":
            del source_data["store"]
            conn.execute(
                text(
                    "UPDATE artefact SET source = :source WHERE id = :id",
                ),
                {"source": source_data, "id": artefact.id},
            )
