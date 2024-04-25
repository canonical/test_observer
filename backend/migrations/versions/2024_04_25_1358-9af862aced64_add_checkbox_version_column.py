"""Add checkbox version column

Revision ID: 9af862aced64
Revises: 624a270a03dc
Create Date: 2024-04-25 13:58:55.894155+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9af862aced64"
down_revision = "624a270a03dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_execution",
        sa.Column(
            "checkbox_version",
            sa.String(length=200),
            nullable=True,
            server_default=None,
        ),
    )


def downgrade() -> None:
    op.drop_column("test_execution", "checkbox_version")
