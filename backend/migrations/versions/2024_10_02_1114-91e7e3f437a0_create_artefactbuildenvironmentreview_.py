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


"""Create ArtefactBuildEnvironmentReview table

Revision ID: 91e7e3f437a0
Revises: 9d7eed94a543
Create Date: 2024-10-02 11:14:42.211503+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "91e7e3f437a0"
down_revision = "9d7eed94a543"
branch_labels = None
depends_on = None


copy_cmd = """
INSERT INTO artefact_build_environment_review (review_decision, review_comment, 
        artefact_build_id, environment_id, created_at, updated_at)
    SELECT review_decision::TEXT[]::artefactbuildenvironmentreviewdecision[], 
        review_comment, artefact_build_id, environment_id, created_at, updated_at
    FROM test_execution
    ORDER BY id
"""

reverse_copy_cmd = """
UPDATE test_execution te
    SET review_comment = aber.review_comment, 
    review_decision = aber.review_decision::TEXT[]::testexecutionreviewdecision[]
    FROM artefact_build_environment_review aber
    WHERE te.environment_id = aber.environment_id 
    AND te.artefact_build_id = aber.artefact_build_id
"""


def upgrade() -> None:
    op.create_table(
        "artefact_build_environment_review",
        sa.Column(
            "review_decision",
            postgresql.ARRAY(
                sa.Enum(
                    "REJECTED",
                    "APPROVED_INCONSISTENT_TEST",
                    "APPROVED_UNSTABLE_PHYSICAL_INFRA",
                    "APPROVED_CUSTOMER_PREREQUISITE_FAIL",
                    "APPROVED_FAULTY_HARDWARE",
                    "APPROVED_ALL_TESTS_PASS",
                    name="artefactbuildenvironmentreviewdecision",
                )
            ),
            nullable=False,
        ),
        sa.Column("review_comment", sa.String(), nullable=False),
        sa.Column("environment_id", sa.Integer(), nullable=False),
        sa.Column("artefact_build_id", sa.Integer(), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artefact_build_id"],
            ["artefact_build.id"],
            name=op.f("artefact_build_environment_review_artefact_build_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["environment_id"],
            ["environment.id"],
            name=op.f("artefact_build_environment_review_environment_id_fkey"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id", name=op.f("artefact_build_environment_review_pkey")
        ),
        sa.UniqueConstraint(
            "artefact_build_id",
            "environment_id",
            name=op.f(
                "artefact_build_environment_review_artefact_build_id_environment_id_key"
            ),
        ),
    )

    op.execute(copy_cmd)


def downgrade() -> None:
    op.execute(reverse_copy_cmd)

    op.drop_table("artefact_build_environment_review")
    op.execute("DROP TYPE artefactbuildenvironmentreviewdecision")
