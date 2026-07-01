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

"""Add artefact filters to attachment rules

Revision ID: 624b22905ce2
Revises: ac1b18650275
Create Date: 2026-06-30 19:21:40.781878+00:00

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "624b22905ce2"
down_revision = "ac1b18650275"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "issue_test_result_attachment_rule",
        sa.Column("artefacts", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
    )
    op.add_column(
        "issue_test_result_attachment_rule",
        sa.Column("artefact_versions", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
    )
    op.add_column(
        "issue_test_result_attachment_rule",
        sa.Column("artefact_stages", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
    )
    op.add_column(
        "issue_test_result_attachment_rule",
        sa.Column("artefact_tracks", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("issue_test_result_attachment_rule", "artefact_tracks")
    op.drop_column("issue_test_result_attachment_rule", "artefact_stages")
    op.drop_column("issue_test_result_attachment_rule", "artefact_versions")
    op.drop_column("issue_test_result_attachment_rule", "artefacts")
