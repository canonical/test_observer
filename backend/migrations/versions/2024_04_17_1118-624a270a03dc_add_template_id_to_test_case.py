"""Add template id to test case

Revision ID: 624a270a03dc
Revises: ae281506fe32
Create Date: 2024-04-17 11:18:27.430695+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "624a270a03dc"
down_revision = "ae281506fe32"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("test_case", sa.Column("template_id", sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_column("test_case", "template_id")
