"""Replace solution-specific fields with attributes

Revision ID: 8202f7b5953e
Revises: eba1d1c92dba
Create Date: 2026-07-21 13:11:39.128081+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "8202f7b5953e"
down_revision = "eba1d1c92dba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("artefact", sa.Column("attributes", postgresql.JSONB(), server_default="{}", nullable=False))
    _assert_no_duplicate_solutions(["name", "version"])
    op.drop_index("unique_solution", table_name="artefact", postgresql_where="(family = 'solution'::familyname)")
    op.create_index(
        "unique_solution", "artefact", ["name", "version"], unique=True, postgresql_where=sa.text("family = 'solution'")
    )
    _remove_bundled_builds()


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
    op.drop_column("artefact", "attributes")


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


def _remove_bundled_builds() -> None:
    _copy_bundled_builds_to_attributes()
    op.drop_table("artefact_bundled_builds_association")
    op.drop_column("artefact", "bundled_builds_hash")


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
    op.execute(
        """
        INSERT INTO artefact_bundled_builds_association (artefact_id, artefact_build_id)
        SELECT a.id, elem::int
        FROM artefact a,
             jsonb_array_elements_text(a.attributes -> 'bundled_builds') AS elem
        WHERE a.attributes ? 'bundled_builds'
        """
    )
