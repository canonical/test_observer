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


"""Add naming conventions

Revision ID: 808f2035f714
Revises: 8317277d4333
Create Date: 2023-12-05 09:51:28.009193+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "808f2035f714"
down_revision = "8317277d4333"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("ix_artefact_name", table_name="artefact")
    op.create_index(op.f("artefact_name_ix"), "artefact", ["name"], unique=False)
    op.drop_index("ix_artefact_build_architecture", table_name="artefact_build")
    op.create_index(
        op.f("artefact_build_architecture_ix"),
        "artefact_build",
        ["architecture"],
        unique=False,
    )
    op.drop_constraint("unique_environment", "environment", type_="unique")
    op.create_unique_constraint(
        op.f("environment_name_architecture_key"),
        "environment",
        ["name", "architecture"],
    )
    op.drop_index("ix_family_name", table_name="family")
    op.create_index(op.f("family_name_ix"), "family", ["name"], unique=True)
    op.drop_index("ix_stage_name", table_name="stage")
    op.create_index(op.f("stage_name_ix"), "stage", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("stage_name_ix"), table_name="stage")
    op.create_index("ix_stage_name", "stage", ["name"], unique=False)
    op.drop_index(op.f("family_name_ix"), table_name="family")
    op.create_index("ix_family_name", "family", ["name"], unique=False)
    op.drop_constraint(
        op.f("environment_name_architecture_key"), "environment", type_="unique"
    )
    op.create_unique_constraint(
        "unique_environment", "environment", ["name", "architecture"]
    )
    op.drop_index(op.f("artefact_build_architecture_ix"), table_name="artefact_build")
    op.create_index(
        "ix_artefact_build_architecture",
        "artefact_build",
        ["architecture"],
        unique=False,
    )
    op.drop_index(op.f("artefact_name_ix"), table_name="artefact")
    op.create_index("ix_artefact_name", "artefact", ["name"], unique=False)
