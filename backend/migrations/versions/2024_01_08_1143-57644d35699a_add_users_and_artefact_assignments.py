"""Add users and artefact assignments

Revision ID: 57644d35699a
Revises: f7b452b19e46
Create Date: 2024-01-08 11:43:04.888342+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "57644d35699a"
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
