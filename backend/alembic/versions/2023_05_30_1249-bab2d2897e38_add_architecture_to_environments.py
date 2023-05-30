"""Add architecture to environments

Revision ID: bab2d2897e38
Revises: 183e6d6df6ff
Create Date: 2023-05-30 12:49:03.545470+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "bab2d2897e38"
down_revision = "183e6d6df6ff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "environment", sa.Column("architecture", sa.String(length=100), nullable=False)
    )
    op.drop_index("ix_environment_name", table_name="environment")
    op.create_unique_constraint(None, "environment", ["name", "architecture"])


def downgrade() -> None:
    op.drop_constraint(None, "environment", type_="unique")
    op.create_index("ix_environment_name", "environment", ["name"], unique=False)
    op.drop_column("environment", "architecture")
