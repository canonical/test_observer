"""Add artefact bug link

Revision ID: ae281506fe32
Revises: 654e57018d35
Create Date: 2024-02-29 07:59:37.397014+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ae281506fe32"
down_revision = "654e57018d35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "artefact",
        sa.Column("bug_link", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("artefact", "bug_link")
