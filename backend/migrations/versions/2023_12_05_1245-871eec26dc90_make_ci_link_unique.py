"""Make ci_link unique

Revision ID: 871eec26dc90
Revises: f59da052cbac
Create Date: 2023-12-05 12:45:25.467951+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "871eec26dc90"
down_revision = "f59da052cbac"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        op.f("test_execution_ci_link_key"), "test_execution", ["ci_link"]
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("test_execution_ci_link_key"), "test_execution", type_="unique"
    )
