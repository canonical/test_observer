"""Add index on test_execution updated_at

Revision ID: eba1d1c92dba
Revises: ac1b18650275
Create Date: 2026-07-02 16:19:59.487151+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "eba1d1c92dba"
down_revision = "ac1b18650275"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("test_execution_updated_at_ix", "test_execution", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("test_execution_updated_at_ix", table_name="test_execution")
