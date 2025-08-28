"""Add user session table

Revision ID: f9faab2e6886
Revises: 592ed147319b
Create Date: 2025-08-28 07:51:39.108239+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f9faab2e6886"
down_revision = "592ed147319b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_session",
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name=op.f("user_session_user_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("user_session_pkey")),
    )
    op.create_index(
        op.f("user_session_user_id_ix"), "user_session", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("user_session_user_id_ix"), table_name="user_session")
    op.drop_table("user_session")
