# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Drop solution-specific bundled build fields

This is the destructive (contract) half of adding the ``attributes`` field
to artefacts and removing the solution-specific fields.
It swaps the ``unique_solution`` index to ``(name, version)`` and drops
``artefact.bundled_builds_hash`` and ``artefact_bundled_builds_association``.

For a safe rolling upgrade this migration must only be deployed *after* the
expand migration (``8202f7b5953e``) and the code that stops using the old fields
have been fully rolled out. It re-runs the backfill first so that any rows
written by not-yet-upgraded units during that rollout (which populate the old
columns but not ``attributes``) are copied over before the columns are dropped.

Revision ID: 8bd1f5009f02
Revises: 8202f7b5953e
Create Date: 2026-08-10 17:16:00.000000+00:00

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8bd1f5009f02"
down_revision = "8202f7b5953e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Catch leftover data written by old code during the rollout of the expand
    # migration before the source columns/table are removed.
    _copy_bundled_builds_to_attributes()
    _assert_no_duplicate_solutions(["name", "version"])
    op.drop_index("unique_solution", table_name="artefact", postgresql_where="(family = 'solution'::familyname)")
    op.create_index(
        "unique_solution", "artefact", ["name", "version"], unique=True, postgresql_where=sa.text("family = 'solution'")
    )
    op.drop_table("artefact_bundled_builds_association")
    op.drop_column("artefact", "bundled_builds_hash")


def downgrade() -> None:
    _add_bundled_builds()
    _assert_no_duplicate_solutions(
        ["name", "source", "version", "track", "stage", "bundled_builds_hash"],
        nullable_columns=["bundled_builds_hash"],
    )
    op.drop_index("unique_solution", table_name="artefact", postgresql_where=sa.text("family = 'solution'"))
    op.create_index(
        "unique_solution",
        "artefact",
        ["name", "source", "version", "track", "stage", "bundled_builds_hash"],
        unique=True,
        postgresql_where="(family = 'solution'::familyname)",
    )


def _assert_no_duplicate_solutions(key_columns: list[str], nullable_columns: list[str] | None = None) -> None:
    """Fail fast with a clear error if applying a unique index on ``key_columns`` (scoped to
    solution artefacts) would violate uniqueness, instead of letting index creation fail with an
    opaque database error.

    Postgres unique indexes treat NULL as distinct from any other value (including another NULL),
    so columns listed in ``nullable_columns`` are excluded from the duplicate search whenever they
    are NULL, matching the semantics of the index we're about to create.
    """
    nullable_columns = nullable_columns or []
    columns_sql = ", ".join(key_columns)
    not_null_clauses = " AND ".join(f"{column} IS NOT NULL" for column in nullable_columns)
    where_clause = f"family = 'solution' AND {not_null_clauses}" if not_null_clauses else "family = 'solution'"

    conn = op.get_bind()
    duplicates = conn.execute(
        sa.text(f"""
            SELECT {columns_sql}, COUNT(*) AS duplicate_count
            FROM artefact
            WHERE {where_clause}
            GROUP BY {columns_sql}
            HAVING COUNT(*) > 1
            LIMIT 5
            """)  # noqa: S608 - key_columns/nullable_columns are fixed, developer-controlled constants
    ).fetchall()

    if duplicates:
        raise RuntimeError(
            f"Cannot create unique index on solutions ({columns_sql}): found existing duplicate rows "
            f"(showing up to 5): {duplicates}. Resolve these duplicates manually before running this migration."
        )


def _add_bundled_builds() -> None:
    op.add_column(
        "artefact", sa.Column("bundled_builds_hash", sa.VARCHAR(length=64), autoincrement=False, nullable=True)
    )
    op.create_table(
        "artefact_bundled_builds_association",
        sa.Column("artefact_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("artefact_build_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["artefact_build_id"],
            ["artefact_build.id"],
            name="artefact_bundled_builds_association_id_fkey",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["artefact_id"], ["artefact.id"], name="artefact_bundled_builds_artefact_id_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("artefact_id", "artefact_build_id", name="artefact_bundled_builds_association_pkey"),
    )
    _restore_bundled_builds_from_attributes()


def _copy_bundled_builds_to_attributes() -> None:
    op.execute(
        """
        UPDATE artefact AS a
        SET attributes = a.attributes
            || jsonb_strip_nulls(
                 jsonb_build_object('bundled_builds_hash', a.bundled_builds_hash)
               )
            || COALESCE(
                 (
                     SELECT jsonb_build_object(
                              'bundled_builds',
                              jsonb_agg(assoc.artefact_build_id ORDER BY assoc.artefact_build_id)
                            )
                     FROM artefact_bundled_builds_association assoc
                     WHERE assoc.artefact_id = a.id
                     HAVING count(*) > 0
                 ),
                 '{}'::jsonb
               )
        WHERE a.bundled_builds_hash IS NOT NULL
           OR EXISTS (
               SELECT 1
               FROM artefact_bundled_builds_association assoc
               WHERE assoc.artefact_id = a.id
           )
        """
    )


def _restore_bundled_builds_from_attributes() -> None:
    op.execute(
        """
        UPDATE artefact AS a
        SET bundled_builds_hash = a.attributes ->> 'bundled_builds_hash'
        WHERE a.attributes ? 'bundled_builds_hash'
        """
    )
    # attributes is API-writable and not schema-validated, so bundled_builds may be a non-array,
    # contain non-numeric elements, or reference unknown build ids. Guard every step so a malformed
    # value can never abort the downgrade:
    #   - the CASE feeding jsonb_array_elements_text ensures it only ever sees an array;
    #   - the CASE around ::int only casts digit-only, in-range strings (NULL otherwise, which the
    #     join drops), avoiding scalar-extraction and invalid-cast/overflow errors;
    #   - the join to artefact_build drops ids that don't correspond to a real build (FK safety).
    op.execute(
        """
        INSERT INTO artefact_bundled_builds_association (artefact_id, artefact_build_id)
        SELECT DISTINCT a.id, ab.id
        FROM artefact a
        CROSS JOIN LATERAL jsonb_array_elements_text(
            CASE
                WHEN jsonb_typeof(a.attributes -> 'bundled_builds') = 'array'
                THEN a.attributes -> 'bundled_builds'
                ELSE '[]'::jsonb
            END
        ) AS elem(value)
        JOIN artefact_build ab
            ON ab.id = CASE
                           WHEN elem.value ~ '^[0-9]+$'
                                AND length(elem.value) <= 10
                                AND elem.value::bigint <= 2147483647
                           THEN elem.value::int
                       END
        """
    )
