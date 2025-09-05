"""Add launchpad teams

Revision ID: f496f12b66b8
Revises: f9faab2e6886
Create Date: 2025-09-05 12:49:49.974922+00:00

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f496f12b66b8"
down_revision = "f9faab2e6886"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "team",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("team_pkey")),
        sa.UniqueConstraint("name", name=op.f("team_name_key")),
    )
    op.create_table(
        "team_users_association",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["team_id"], ["team.id"], name=op.f("team_users_association_team_id_fkey")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["app_user.id"],
            name=op.f("team_users_association_user_id_fkey"),
        ),
        sa.PrimaryKeyConstraint(
            "user_id", "team_id", name=op.f("team_users_association_pkey")
        ),
    )


def downgrade() -> None:
    op.drop_table("team_users_association")
    op.drop_table("team")
