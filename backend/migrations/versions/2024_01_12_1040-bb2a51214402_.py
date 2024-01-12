"""empty message

Revision ID: bb2a51214402
Revises: c9851b127edc
Create Date: 2024-01-12 10:40:00.596887+00:00

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "bb2a51214402"
down_revision = "c9851b127edc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER TABLE "user" RENAME TO app_user')
    op.drop_constraint("user_launchpad_email_key", "app_user", type_="unique")
    op.create_unique_constraint(
        op.f("app_user_launchpad_email_key"), "app_user", ["launchpad_email"]
    )


def downgrade() -> None:
    op.execute('ALTER TABLE app_user RENAME TO "user"')
    op.drop_constraint(op.f("app_user_launchpad_email_key"), "user", type_="unique")
    op.create_unique_constraint("user_launchpad_email_key", "user", ["launchpad_email"])
