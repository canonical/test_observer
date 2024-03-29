"""Remove is_archived, will use a view

Revision ID: 183e6d6df6ff
Revises: 12383cab7248
Create Date: 2023-05-29 09:17:37.129881+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "183e6d6df6ff"
down_revision = "12383cab7248"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("artefact", "is_archived")


def downgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column("is_archived", sa.BOOLEAN(), autoincrement=False, nullable=False),
    )
