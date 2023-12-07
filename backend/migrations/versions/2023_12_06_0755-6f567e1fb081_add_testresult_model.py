"""Add TestResult model

Revision ID: 6f567e1fb081
Revises: 871eec26dc90
Create Date: 2023-12-06 07:55:11.163965+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6f567e1fb081"
down_revision = "871eec26dc90"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "test_result",
        sa.Column("c3_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PASSED", "FAILED", "SKIPPED", name="testresultstatus"),
            nullable=False,
        ),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("comment", sa.String(), nullable=False),
        sa.Column("io_log", sa.String(), nullable=False),
        sa.Column("test_execution_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["test_execution_id"],
            ["test_execution.id"],
            name=op.f("test_result_test_execution_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("test_result_pkey")),
    )
    op.create_index(
        op.f("test_result_test_execution_id_ix"),
        "test_result",
        ["test_execution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_result_test_execution_id_ix"), table_name="test_result")
    op.drop_table("test_result")
    op.execute("DROP TYPE testresultstatus")
