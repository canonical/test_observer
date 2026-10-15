# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

"""Cascade test execution metadata association rows on deletion

Revision ID: b2db87f4400c
Revises: 6cf2ad72a55e
Create Date: 2026-10-07 12:01:00.000000+00:00

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2db87f4400c"
down_revision = "6cf2ad72a55e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        op.f("test_execution_metadata_association_table_test_execution_id_fkey"),
        "test_execution_metadata_association_table",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("test_execution_metadata_association_table_test_execution_id_fkey"),
        "test_execution_metadata_association_table",
        "test_execution",
        ["test_execution_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        op.f("test_execution_metadata_association_table_test_execution_metadata_id_fkey"),
        "test_execution_metadata_association_table",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("test_execution_metadata_association_table_test_execution_metadata_id_fkey"),
        "test_execution_metadata_association_table",
        "test_execution_metadata",
        ["test_execution_metadata_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("test_execution_metadata_association_table_test_execution_metadata_id_fkey"),
        "test_execution_metadata_association_table",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("test_execution_metadata_association_table_test_execution_metadata_id_fkey"),
        "test_execution_metadata_association_table",
        "test_execution_metadata",
        ["test_execution_metadata_id"],
        ["id"],
    )
    op.drop_constraint(
        op.f("test_execution_metadata_association_table_test_execution_id_fkey"),
        "test_execution_metadata_association_table",
        type_="foreignkey",
    )
    op.create_foreign_key(
        op.f("test_execution_metadata_association_table_test_execution_id_fkey"),
        "test_execution_metadata_association_table",
        "test_execution",
        ["test_execution_id"],
        ["id"],
    )
