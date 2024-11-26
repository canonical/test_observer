"""Allow multiple TestExecution runs

Revision ID: 063e32aac8db
Revises: b234def463ad
Create Date: 2024-10-21 10:35:17.364462+00:00

"""
from textwrap import dedent

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "063e32aac8db"
down_revision = "b234def463ad"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "test_execution_artefact_build_id_environment_id_key",
        "test_execution",
        type_="unique",
    )


def downgrade() -> None:
    remove_test_execution_runs_keeping_latest()

    op.create_unique_constraint(
        "test_execution_artefact_build_id_environment_id_key",
        "test_execution",
        ["artefact_build_id", "environment_id"],
    )


def remove_test_execution_runs_keeping_latest():
    connection = op.get_bind()

    stmt = """\
        SELECT artefact_build_id, environment_id, MAX(id), COUNT(*)
        FROM test_execution
        GROUP BY artefact_build_id, environment_id
        HAVING COUNT(*) > 1
    """

    for ab_id, e_id, max_id, _ in connection.execute(sa.text(dedent(stmt))):
        stmt = f"""\
            DELETE FROM test_execution
            WHERE artefact_build_id={ab_id} AND environment_id={e_id} AND id <> {max_id}
        """
        op.execute(dedent(stmt))
