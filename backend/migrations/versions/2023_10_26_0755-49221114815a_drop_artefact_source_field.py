"""Drop Artefact source field

Revision ID: 49221114815a
Revises: d646a347472e
Create Date: 2023-10-26 07:55:27.449425+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "49221114815a"
down_revision = "d646a347472e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("artefact", "source")


def downgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    artefact_table = sa.table(
        "artefact",
        sa.column("id", sa.Integer()),
        sa.column("track", sa.String()),
        sa.column("store", sa.String()),
        sa.column("series", sa.String()),
        sa.column("repo", sa.String()),
        sa.column("source", postgresql.JSONB(astext_type=sa.Text())),
    )

    conn = op.get_bind()
    for artefact in conn.execute(sa.select(artefact_table)):
        source = {
            k: getattr(artefact, k)
            for k in ["track", "store", "series", "repo"]
            if getattr(artefact, k) is not None
        }

        conn.execute(
            sa.update(artefact_table)
            .where(artefact_table.c.id == artefact.id)
            .values(source=source)
        )

    op.alter_column("artefact", "source", nullable=False)
