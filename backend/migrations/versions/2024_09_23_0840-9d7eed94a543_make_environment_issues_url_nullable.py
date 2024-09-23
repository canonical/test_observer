"""Make environment issues URL nullable

Revision ID: 9d7eed94a543
Revises: 505b96fd7731
Create Date: 2024-09-23 08:40:44.972779+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9d7eed94a543"
down_revision = "505b96fd7731"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "environment_issue", "url", existing_type=sa.VARCHAR(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "environment_issue", "url", existing_type=sa.VARCHAR(), nullable=False
    )
