"""Add users and assignees

Revision ID: 0d132a319118
Revises: f7b452b19e46
Create Date: 2024-01-09 07:33:48.475046+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0d132a319118"
down_revision = "f7b452b19e46"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("launchpad_handle", sa.String(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("user_pkey")),
        sa.UniqueConstraint("launchpad_handle", name=op.f("user_launchpad_handle_key")),
    )
    op.add_column("artefact", sa.Column("assignee_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("artefact_assignee_id_fkey"), "artefact", "user", ["assignee_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("artefact_assignee_id_fkey"), "artefact", type_="foreignkey"
    )
    op.drop_column("artefact", "assignee_id")
    op.drop_table("user")
