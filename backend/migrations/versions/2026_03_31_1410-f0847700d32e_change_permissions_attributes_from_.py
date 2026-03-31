"""Change permissions attributes from string to enum

Revision ID: f0847700d32e
Revises: c29b4f545a9b
Create Date: 2026-03-31 14:10:46.747275+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f0847700d32e'
down_revision = 'c29b4f545a9b'
branch_labels = None
depends_on = None

PERMISSION_TYPE = postgresql.ARRAY(postgresql.ENUM(name="permission"))

def upgrade() -> None:
    # upgrade application table
    op.alter_column('application', 'permissions',
               existing_type=postgresql.ARRAY(sa.VARCHAR()),
               type_=PERMISSION_TYPE,
               existing_nullable=False,
               postgresql_using="permissions::permission[]")

    # upgrade team table
    # drop default to prevent casting errors from postgresql
    op.execute("ALTER TABLE team ALTER COLUMN permissions DROP DEFAULT")

    # change type
    op.alter_column('team', 'permissions',
               existing_type=postgresql.ARRAY(sa.VARCHAR()),
               type_=PERMISSION_TYPE,
               existing_nullable=False,
               postgresql_using="permissions::permission[]")

    # apply new default
    op.execute("ALTER TABLE team ALTER COLUMN permissions SET DEFAULT '{}'::permission[]")


def downgrade() -> None:
    # downgrade team table
    # drop default
    op.execute("ALTER TABLE team ALTER COLUMN permissions DROP DEFAULT")

    # convert
    op.alter_column('team', 'permissions',
               existing_type=PERMISSION_TYPE,
               type_=postgresql.ARRAY(sa.VARCHAR()),
               existing_nullable=False,
               postgresql_using="permissions::varchar[]")

    # restore previous default
    op.execute("ALTER TABLE team ALTER COLUMN permissions SET DEFAULT '{}'::character varying[]")

    # upgrade application table
    op.alter_column('application', 'permissions',
               existing_type=PERMISSION_TYPE,
               type_=postgresql.ARRAY(sa.VARCHAR()),
               existing_nullable=False,
               postgresql_using="permissions::varchar[]")
