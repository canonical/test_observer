"""Drop review columns from Test Execution Table

Revision ID: b234def463ad
Revises: 91e7e3f437a0
Create Date: 2024-10-18 11:34:38.285303+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b234def463ad"
down_revision = "91e7e3f437a0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("test_execution", "review_decision")
    op.drop_column("test_execution", "review_comment")
    op.execute("DROP TYPE testexecutionreviewdecision")


def downgrade() -> None:
    te_review_decision = sa.Enum(
        "REJECTED",
        "APPROVED_INCONSISTENT_TEST",
        "APPROVED_UNSTABLE_PHYSICAL_INFRA",
        "APPROVED_FAULTY_HARDWARE",
        "APPROVED_CUSTOMER_PREREQUISITE_FAIL",
        "APPROVED_ALL_TESTS_PASS",
        name="testexecutionreviewdecision",
    )
    te_review_decision.create(op.get_bind())
    op.add_column(
        "test_execution",
        sa.Column(
            "review_comment",
            sa.VARCHAR(),
            server_default=sa.text("''::character varying"),
            autoincrement=False,
            nullable=False,
        ),
    )
    op.add_column(
        "test_execution",
        sa.Column(
            "review_decision",
            postgresql.ARRAY(te_review_decision),
            server_default=sa.text("'{}'::testexecutionreviewdecision[]"),
            autoincrement=False,
            nullable=False,
        ),
    )
