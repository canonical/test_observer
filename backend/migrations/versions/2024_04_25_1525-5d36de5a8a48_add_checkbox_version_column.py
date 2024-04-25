"""Add checkbox version column

Revision ID: 5d36de5a8a48
Revises: 624a270a03dc
Create Date: 2024-04-25 15:25:33.149465+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5d36de5a8a48"
down_revision = "624a270a03dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_execution",
        sa.Column("checkbox_version", sa.String(length=200), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("test_execution", "checkbox_version")
