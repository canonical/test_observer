# Copyright (C) 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Add image family

Revision ID: 121edad6b53f
Revises: 7878a1b29384
Create Date: 2025-01-08 13:12:05.831020+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "121edad6b53f"
down_revision = "7878a1b29384"
branch_labels = None
depends_on = None


def upgrade() -> None:
    add_image_family()
    add_new_stages()

    add_os_column()
    add_release_column()
    add_sha256_column()
    add_owner_column()
    add_image_url_column()


def add_image_family():
    op.execute("ALTER TYPE familyname ADD VALUE IF NOT EXISTS 'image'")


def add_new_stages():
    op.execute("ALTER TYPE stagename ADD VALUE IF NOT EXISTS 'pending'")
    op.execute("ALTER TYPE stagename ADD VALUE IF NOT EXISTS 'current'")


def add_os_column():
    op.add_column("artefact", sa.Column("os", sa.String(length=200)))
    op.execute("UPDATE artefact SET os = '' WHERE os is NULL")
    op.alter_column("artefact", "os", nullable=False)


def add_release_column():
    op.add_column("artefact", sa.Column("release", sa.String(length=200)))
    op.execute("UPDATE artefact SET release = '' WHERE release is NULL")
    op.alter_column("artefact", "release", nullable=False)


def add_sha256_column():
    op.add_column("artefact", sa.Column("sha256", sa.String(length=200)))
    op.execute("UPDATE artefact SET sha256 = '' WHERE sha256 is NULL")
    op.alter_column("artefact", "sha256", nullable=False)


def add_owner_column():
    op.add_column("artefact", sa.Column("owner", sa.String(length=200)))
    op.execute("UPDATE artefact SET owner = '' WHERE owner is NULL")
    op.alter_column("artefact", "owner", nullable=False)


def add_image_url_column():
    op.add_column("artefact", sa.Column("image_url", sa.String(length=200)))
    op.execute("UPDATE artefact SET image_url = '' WHERE image_url is NULL")
    op.alter_column("artefact", "image_url", nullable=False)


def downgrade() -> None:
    op.execute("DELETE FROM artefact WHERE family = 'image'")
    op.drop_column("artefact", "owner")
    op.drop_column("artefact", "sha256")
    op.drop_column("artefact", "release")
    op.drop_column("artefact", "os")
    op.drop_column("artefact", "image_url")

    remove_image_family_enum_value()
    remove_added_stage_enum_values()


def remove_image_family_enum_value():
    op.execute("ALTER TYPE familyname RENAME TO familyname_old")
    op.execute("CREATE TYPE familyname AS " "ENUM('snap', 'deb', 'charm')")
    op.execute(
        "ALTER TABLE artefact ALTER COLUMN family TYPE "
        "familyname USING family::text::familyname"
    )
    op.execute("DROP TYPE familyname_old")


def remove_added_stage_enum_values():
    op.execute("ALTER TYPE stagename RENAME TO stagename_old")
    op.execute(
        "CREATE TYPE stagename AS "
        "ENUM('edge', 'beta', 'candidate', 'stable', 'proposed', 'updates')"
    )
    op.execute(
        "ALTER TABLE artefact ALTER COLUMN stage TYPE "
        "stagename USING stage::text::stagename"
    )
    op.execute("DROP TYPE stagename_old")
