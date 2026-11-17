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

"""Replace family enum columns with family references

Revision ID: ad7acb807c63
Revises: 914619eedf53
Create Date: 2026-11-17 15:20:08.519916+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "ad7acb807c63"
down_revision = "914619eedf53"
branch_labels = None
depends_on = None

family_enum = postgresql.ENUM("snap", "deb", "charm", "image", "solution", name="familyname", create_type=False)
family_indexes = (
    ("unique_snap", ["name", "version", "track", "branch"], "snap"),
    ("unique_charm", ["name", "version", "track", "branch"], "charm"),
    ("unique_deb", ["name", "version", "series", "repo", "source"], "deb"),
    ("unique_image", ["sha256"], "image"),
    ("unique_solution", ["name", "version"], "solution"),
)


def _drop_family_indexes() -> None:
    for name, _, _ in family_indexes:
        op.drop_index(name, table_name="artefact")


def _create_family_indexes() -> None:
    for name, columns, family in family_indexes:
        op.create_index(name, "artefact", columns, unique=True, postgresql_where=sa.text(f"family = '{family}'"))


def upgrade() -> None:
    _drop_family_indexes()
    op.alter_column(
        "artefact",
        "family",
        existing_type=family_enum,
        type_=sa.String(100),
        existing_nullable=False,
        postgresql_using="family::text",
    )
    op.create_foreign_key(op.f("artefact_family_fkey"), "artefact", "family", ["family"], ["name"])
    op.alter_column(
        "artefact_audit",
        "family",
        existing_type=family_enum,
        type_=sa.String(100),
        existing_nullable=True,
        postgresql_using="family::text",
    )
    op.alter_column(
        "artefact_matching_rule",
        "family",
        existing_type=family_enum,
        type_=sa.String(100),
        existing_nullable=False,
        postgresql_using="family::text",
    )
    op.create_foreign_key(
        op.f("artefact_matching_rule_family_fkey"), "artefact_matching_rule", "family", ["family"], ["name"]
    )
    op.alter_column(
        "issue_test_result_attachment_rule",
        "families",
        existing_type=postgresql.ARRAY(family_enum),
        type_=postgresql.ARRAY(sa.String()),
        existing_nullable=False,
        postgresql_using="families::text[]",
    )
    _create_family_indexes()


def downgrade() -> None:
    _drop_family_indexes()
    op.alter_column(
        "issue_test_result_attachment_rule",
        "families",
        existing_type=postgresql.ARRAY(sa.String()),
        type_=postgresql.ARRAY(family_enum),
        existing_nullable=False,
        postgresql_using="families::text[]::familyname[]",
    )
    op.drop_constraint(op.f("artefact_matching_rule_family_fkey"), "artefact_matching_rule", type_="foreignkey")
    op.alter_column(
        "artefact_matching_rule",
        "family",
        existing_type=sa.String(100),
        type_=family_enum,
        existing_nullable=False,
        postgresql_using="family::text::familyname",
    )
    op.alter_column(
        "artefact_audit",
        "family",
        existing_type=sa.String(100),
        type_=family_enum,
        existing_nullable=True,
        postgresql_using="family::text::familyname",
    )
    op.drop_constraint(op.f("artefact_family_fkey"), "artefact", type_="foreignkey")
    op.alter_column(
        "artefact",
        "family",
        existing_type=sa.String(100),
        type_=family_enum,
        existing_nullable=False,
        postgresql_using="family::text::familyname",
    )
    _create_family_indexes()
