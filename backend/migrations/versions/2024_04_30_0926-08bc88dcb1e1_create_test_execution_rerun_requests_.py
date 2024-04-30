"""Create test execution rerun requests table

Revision ID: 08bc88dcb1e1
Revises: 624a270a03dc
Create Date: 2024-04-30 09:26:48.766175+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "08bc88dcb1e1"
down_revision = "624a270a03dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_execution_rerun_request",
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_execution_rerun_request_test_execution_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("test_execution_rerun_request_pkey")),
        sa.UniqueConstraint(
            "test_execution_id",
            name=op.f("test_execution_rerun_request_test_execution_id_key"),
        ),
    )


def downgrade() -> None:
    op.drop_table("test_execution_rerun_request")
