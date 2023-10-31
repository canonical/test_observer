"""Copy Artefact.source into track, store, series & repo

Revision ID: 38807948d269
Revises: cb121ad343dd
Create Date: 2023-10-25 12:33:03.206702+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "38807948d269"
down_revision = "cb121ad343dd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    artefact_table = sa.table(
        "artefact",
        sa.column("id", sa.Integer()),
        sa.column("source", sa.JSON()),
        sa.column("track", sa.String()),
        sa.column("store", sa.String()),
        sa.column("series", sa.String()),
        sa.column("repo", sa.String()),
    )

    conn = op.get_bind()
    get_artefacts_id_source = sa.select(artefact_table.c.id, artefact_table.c.source)
    for id, source in conn.execute(get_artefacts_id_source):
        conn.execute(
            sa.update(artefact_table)
            .where(artefact_table.c.id == id)
            .values(
                track=source.get("track"),
                store=source.get("store"),
                series=source.get("series"),
                repo=source.get("repo"),
            )
        )


def downgrade() -> None:
    artefact_table = sa.table(
        "artefact",
        sa.column("track", sa.String()),
        sa.column("store", sa.String()),
        sa.column("series", sa.String()),
        sa.column("repo", sa.String()),
    )

    conn = op.get_bind()
    conn.execute(
        sa.update(artefact_table).values(
            track=None,
            store=None,
            series=None,
            repo=None,
        )
    )
