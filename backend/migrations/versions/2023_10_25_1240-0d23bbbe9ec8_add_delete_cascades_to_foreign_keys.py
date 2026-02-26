# Copyright 2023 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Add delete cascades to foreign keys

Revision ID: 0d23bbbe9ec8
Revises: 38807948d269
Create Date: 2023-10-25 12:40:53.807999+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0d23bbbe9ec8"
down_revision = "38807948d269"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("artefact_stage_id_fkey", "artefact", type_="foreignkey")
    op.create_foreign_key(
        "artefact_stage_id_fkey",
        "artefact",
        "stage",
        ["stage_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("artefact_build_artefact_id_fkey", "artefact_build", type_="foreignkey")
    op.create_foreign_key(
        "artefact_build_artefact_id_fkey",
        "artefact_build",
        "artefact",
        ["artefact_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("stage_family_id_fkey", "stage", type_="foreignkey")
    op.create_foreign_key(
        "stage_family_id_fkey",
        "stage",
        "family",
        ["family_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint("test_execution_artefact_build_id_fkey", "test_execution", type_="foreignkey")
    op.create_foreign_key(
        "test_execution_artefact_build_id_fkey",
        "test_execution",
        "artefact_build",
        ["artefact_build_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("test_execution_artefact_build_id_fkey", "test_execution", type_="foreignkey")
    op.create_foreign_key(
        "test_execution_artefact_build_id_fkey",
        "test_execution",
        "artefact_build",
        ["artefact_build_id"],
        ["id"],
    )
    op.drop_constraint("stage_family_id_fkey", "stage", type_="foreignkey")
    op.create_foreign_key("stage_family_id_fkey", "stage", "family", ["family_id"], ["id"])
    op.drop_constraint("artefact_build_artefact_id_fkey", "artefact_build", type_="foreignkey")
    op.create_foreign_key(
        "artefact_build_artefact_id_fkey",
        "artefact_build",
        "artefact",
        ["artefact_id"],
        ["id"],
    )
    op.drop_constraint("artefact_stage_id_fkey", "artefact", type_="foreignkey")
    op.create_foreign_key("artefact_stage_id_fkey", "artefact", "stage", ["stage_id"], ["id"])
