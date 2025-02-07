# Copyright (C) 2023-2025 Canonical Ltd.
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


"""Add indexes on relations that don't have them

Revision ID: b3b376fb6353
Revises: 063e32aac8db
Create Date: 2024-12-03 13:02:41.364193+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b3b376fb6353"
down_revision = "063e32aac8db"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        op.f("artefact_assignee_id_ix"),
        "artefact",
        ["assignee_id"],
        unique=False,
    )
    op.create_index(
        op.f("artefact_stage_id_ix"),
        "artefact",
        ["stage_id"],
        unique=False,
    )
    op.create_index(
        op.f("artefact_build_artefact_id_ix"),
        "artefact_build",
        ["artefact_id"],
        unique=False,
    )
    op.create_index(
        op.f("artefact_build_environment_review_artefact_build_id_ix"),
        "artefact_build_environment_review",
        ["artefact_build_id"],
        unique=False,
    )
    op.create_index(
        op.f("artefact_build_environment_review_environment_id_ix"),
        "artefact_build_environment_review",
        ["environment_id"],
        unique=False,
    )
    op.create_index(
        op.f("stage_family_id_ix"),
        "stage",
        ["family_id"],
        unique=False,
    )
    op.create_index(
        op.f("test_event_test_execution_id_ix"),
        "test_event",
        ["test_execution_id"],
        unique=False,
    )
    op.create_index(
        op.f("test_execution_artefact_build_id_ix"),
        "test_execution",
        ["artefact_build_id"],
        unique=False,
    )
    op.create_index(
        op.f("test_execution_environment_id_ix"),
        "test_execution",
        ["environment_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("test_execution_environment_id_ix"), table_name="test_execution")
    op.drop_index(
        op.f("test_execution_artefact_build_id_ix"), table_name="test_execution"
    )
    op.drop_index(op.f("test_event_test_execution_id_ix"), table_name="test_event")
    op.drop_index(op.f("stage_family_id_ix"), table_name="stage")
    op.drop_index(
        op.f("artefact_build_environment_review_environment_id_ix"),
        table_name="artefact_build_environment_review",
    )
    op.drop_index(
        op.f("artefact_build_environment_review_artefact_build_id_ix"),
        table_name="artefact_build_environment_review",
    )
    op.drop_index(op.f("artefact_build_artefact_id_ix"), table_name="artefact_build")
    op.drop_index(op.f("artefact_stage_id_ix"), table_name="artefact")
    op.drop_index(op.f("artefact_assignee_id_ix"), table_name="artefact")
