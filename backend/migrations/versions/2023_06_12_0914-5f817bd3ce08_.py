"""Add latest artefacts view

Revision ID: 5f817bd3ce08
Revises: 6a80dad01d24
Create Date: 2023-06-12 09:14:15.560032+00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "5f817bd3ce08"
down_revision = "6a80dad01d24"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIEW latest_artefacts_view AS
        SELECT a.*
        FROM artefact a
        JOIN stage s ON a.stage_id = s.id
        JOIN (
            SELECT stage_id, name, source, MAX(created_at) AS max_created
            FROM artefact
            GROUP BY stage_id, name, source
       ) AS sq ON a.stage_id = sq.stage_id
         AND a.name = sq.name
         AND a.source = sq.source
         AND a.created_at = sq.max_created
    """
    )


def downgrade() -> None:
    op.execute("DROP VIEW latest_artefacts_view")
