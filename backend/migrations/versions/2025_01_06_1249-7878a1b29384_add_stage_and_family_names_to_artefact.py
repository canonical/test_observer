# Copyright (C) 2023 Canonical Ltd.
#
# This file is part of Test Observer Backend.
#
# Test Observer Backend is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# Test Observer Backend is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


"""Add stage and family names to artefact

Revision ID: 7878a1b29384
Revises: 0e09759a33c3
Create Date: 2025-01-06 12:49:42.039170+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7878a1b29384"
down_revision = "0e09759a33c3"
branch_labels = None
depends_on = None


family_type = sa.Enum("snap", "deb", "charm", name="familyname")
stage_type = sa.Enum(
    "proposed", "updates", "edge", "beta", "candidate", "stable", name="stagename"
)


fill_stages_stmt = f"""
UPDATE artefact
SET stage = subq.name::{stage_type.name}
FROM (SELECT id, name FROM stage) as subq
WHERE subq.id = artefact.stage_id
"""

fill_families_stmt = f"""
UPDATE artefact
SET family = subq.family::{family_type.name}
FROM (
    SELECT stage.id stage_id, family.name family
    FROM stage 
    JOIN family ON family.id = stage.family_id
) subq
WHERE subq.stage_id = artefact.stage_id
"""


def upgrade() -> None:
    _add_artefact_stage_field()
    _add_artefact_family_field()
    _drop_artefact_stage_id_field()
    _drop_stage_table()
    _drop_family_table()


def _add_artefact_stage_field() -> None:
    stage_type.create(op.get_bind())
    op.add_column("artefact", sa.Column("stage", stage_type))
    op.execute(fill_stages_stmt)
    op.alter_column("artefact", "stage", nullable=False)


def _add_artefact_family_field() -> None:
    family_type.create(op.get_bind())
    op.add_column(
        "artefact",
        sa.Column("family", family_type),
    )
    op.execute(fill_families_stmt)
    op.alter_column("artefact", "family", nullable=False)


def _drop_artefact_stage_id_field() -> None:
    op.drop_index("artefact_stage_id_ix", table_name="artefact")
    op.drop_constraint("artefact_stage_id_fkey", "artefact", type_="foreignkey")
    op.drop_column("artefact", "stage_id")


def _drop_family_table() -> None:
    op.drop_index("family_name_ix", table_name="family")
    op.drop_table("family")


def _drop_stage_table() -> None:
    op.drop_index("stage_family_id_ix", table_name="stage")
    op.drop_index("stage_name_ix", table_name="stage")
    op.drop_table("stage")


fill_stage_id_stmt = """
UPDATE artefact
SET stage_id = subq.stage_id
FROM (
    SELECT stage.id stage_id, stage.name stage_name, family.name family_name
    FROM stage
    JOIN family ON family.id = stage.family_id
) subq
WHERE subq.stage_name = artefact.stage::text 
    AND subq.family_name = artefact.family::text
"""


def downgrade() -> None:
    family_table = _create_family_table()
    stage_table = _create_stage_table()
    _fill_tables(family_table, stage_table)
    _add_artefact_stage_id_field()
    _drop_family_column()
    _drop_stage_column()


def _create_stage_table() -> sa.Table:
    result = op.create_table(
        "stage",
        sa.Column("name", sa.VARCHAR(length=100), autoincrement=False, nullable=False),
        sa.Column("position", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("family_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["family_id"],
            ["family.id"],
            name="stage_family_id_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="stage_pkey"),
    )
    op.create_index("stage_name_ix", "stage", ["name"], unique=False)
    op.create_index("stage_family_id_ix", "stage", ["family_id"], unique=False)
    return result


def _create_family_table() -> sa.Table:
    result = op.create_table(
        "family",
        sa.Column("name", sa.VARCHAR(length=100), autoincrement=False, nullable=False),
        sa.Column(
            "id",
            sa.INTEGER(),
            server_default=sa.text("nextval('family_id_seq'::regclass)"),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "created_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.Column(
            "updated_at", postgresql.TIMESTAMP(), autoincrement=False, nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="family_pkey"),
        postgresql_ignore_search_path=False,
    )
    op.create_index("family_name_ix", "family", ["name"], unique=True)
    return result


def _fill_tables(family_table: sa.Table, stage_table: sa.Table) -> None:
    conn = op.get_bind()
    families_and_stages = {
        "snap": ["edge", "beta", "candidate", "stable"],
        "deb": ["proposed", "updates"],
        "charm": ["edge", "beta", "candidate", "stable"],
    }

    for family in families_and_stages:
        (inserted_family,) = conn.execute(
            sa.insert(family_table)
            .values(
                name=family,
                created_at=sa.func.now(),
                updated_at=sa.func.now(),
            )
            .returning(family_table.c.id)
        )
        stage_position = 10
        for stage in families_and_stages[family]:
            conn.execute(
                sa.insert(stage_table).values(
                    name=stage,
                    family_id=inserted_family.id,
                    position=stage_position,
                    created_at=sa.func.now(),
                    updated_at=sa.func.now(),
                )
            )
            stage_position += 10


def _add_artefact_stage_id_field() -> None:
    op.add_column(
        "artefact",
        sa.Column("stage_id", sa.INTEGER(), autoincrement=False),
    )

    op.execute(fill_stage_id_stmt)
    op.alter_column("artefact", "stage_id", nullable=False)
    op.create_foreign_key(
        "artefact_stage_id_fkey",
        "artefact",
        "stage",
        ["stage_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("artefact_stage_id_ix", "artefact", ["stage_id"], unique=False)


def _drop_family_column() -> None:
    op.drop_column("artefact", "family")
    op.execute(f"DROP TYPE IF EXISTS {family_type.name}")


def _drop_stage_column() -> None:
    op.drop_column("artefact", "stage")
    op.execute(f"DROP TYPE IF EXISTS {stage_type.name}")
