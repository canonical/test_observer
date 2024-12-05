"""Add test plan to test execution

Revision ID: 4c2e5946358c
Revises: b3b376fb6353
Create Date: 2024-12-05 10:00:53.848151+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "4c2e5946358c"
down_revision = "b3b376fb6353"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "test_execution",
        sa.Column(
            "test_plan",
            sa.String(length=200),
            nullable=True,
        ),
    )

    op.execute("UPDATE test_execution SET test_plan = ''")

    op.execute("ALTER TABLE test_execution ALTER COLUMN test_plan SET NOT NULL")


def downgrade() -> None:
    op.drop_column("test_execution", "test_plan")
