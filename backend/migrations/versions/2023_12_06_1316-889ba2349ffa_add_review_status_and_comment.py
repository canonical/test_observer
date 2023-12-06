"""Add review status and comment

Revision ID: 889ba2349ffa
Revises: 871eec26dc90
Create Date: 2023-12-06 13:16:07.171288+00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '889ba2349ffa'
down_revision = '871eec26dc90'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE test_execution_review_status_enum AS "
        "ENUM('APPROVED_FLAKY_TESTS', 'APPROVED_PROVISION_ERRORS', "
        "'APPROVED', 'MARKED_AS_FAILED', 'UNDECIDED')"
    )
    op.execute(
        "ALTER TABLE test_execution ADD COLUMN "
        "review_status test_execution_review_status_enum"
    )
    op.add_column(
        "test_execution", sa.Column("review_comment", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("test_execution", "review_comment")
    op.drop_column("test_execution", "review_status")
    op.execute("DROP TYPE test_execution_review_status_enum")
