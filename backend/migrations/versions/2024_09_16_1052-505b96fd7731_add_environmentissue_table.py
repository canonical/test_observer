"""Add EnvironmentIssue table

Revision ID: 505b96fd7731
Revises: ba6550a03bc8
Create Date: 2024-09-16 10:52:25.226261+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "505b96fd7731"
down_revision = "ba6550a03bc8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "environment_issue",
        sa.Column("environment_name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("environment_issue_pkey")),
    )


def downgrade() -> None:
    op.drop_table("environment_issue")
