"""Make artefact track, store, series and repo not nullable

Revision ID: 654e57018d35
Revises: bb2a51214402
Create Date: 2024-02-20 08:19:37.117290+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "654e57018d35"
down_revision = "bb2a51214402"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("unique_deb", "artefact", type_="unique")
    op.create_index(
        "unique_deb",
        "artefact",
        ["name", "version", "series", "repo"],
        unique=True,
        postgresql_where=sa.text("series != '' AND repo != ''"),
    )
    op.drop_constraint("unique_snap", "artefact", type_="unique")
    op.create_index(
        "unique_snap",
        "artefact",
        ["name", "version", "track"],
        unique=True,
        postgresql_where=sa.text("track != ''"),
    )

    op.execute("UPDATE artefact SET track = '' WHERE track is NULL")
    op.execute("UPDATE artefact SET store = '' WHERE store is NULL")
    op.execute("UPDATE artefact SET series = '' WHERE series is NULL")
    op.execute("UPDATE artefact SET repo = '' WHERE repo is NULL")

    op.alter_column("artefact", "track", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("artefact", "store", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("artefact", "series", existing_type=sa.VARCHAR(), nullable=False)
    op.alter_column("artefact", "repo", existing_type=sa.VARCHAR(), nullable=False)


def downgrade() -> None:
    op.alter_column("artefact", "repo", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("artefact", "series", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("artefact", "store", existing_type=sa.VARCHAR(), nullable=True)
    op.alter_column("artefact", "track", existing_type=sa.VARCHAR(), nullable=True)

    op.execute("UPDATE artefact SET repo = NULL WHERE repo = ''")
    op.execute("UPDATE artefact SET series = NULL WHERE series = ''")
    op.execute("UPDATE artefact SET store = NULL WHERE store = ''")
    op.execute("UPDATE artefact SET track = NULL WHERE track = ''")

    op.drop_index(
        "unique_snap", table_name="artefact", postgresql_where=sa.text("track != ''")
    )
    op.create_unique_constraint("unique_snap", "artefact", ["name", "version", "track"])
    op.drop_index(
        "unique_deb",
        table_name="artefact",
        postgresql_where=sa.text("series != '' AND repo != ''"),
    )
    op.create_unique_constraint(
        "unique_deb", "artefact", ["name", "version", "series", "repo"]
    )
