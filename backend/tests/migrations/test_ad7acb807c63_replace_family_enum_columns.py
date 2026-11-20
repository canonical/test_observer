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

from collections.abc import Generator
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import ARRAY, Connection, Engine, Enum, MetaData, Table, create_engine, make_url, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy_utils import create_database, drop_database  # type: ignore[import-untyped]

from test_observer.data_access.audit import set_connection_audit_context
from test_observer.data_access.models import Base
from test_observer.data_access.models_enums import IssueSource

PREVIOUS_REV = "914619eedf53"
TARGET_REV = "ad7acb807c63"
LEGACY_FAMILIES = ("snap", "deb", "charm", "image", "solution")


@pytest.fixture
def migration_context(db_url: str) -> Generator[tuple[Engine, Config], None, None]:
    url = make_url(db_url).set(database=f"test_family_columns_{uuid4().hex}")
    create_database(url)
    engine = create_engine(url)
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
    try:
        command.upgrade(config, PREVIOUS_REV)
        yield engine, config
    finally:
        engine.dispose()
        drop_database(url)


def _assert_unique_indexes(connection: Connection, artefacts: Table, phase: str) -> None:
    for family in LEGACY_FAMILIES:
        values = {
            "name": f"{phase}-{family}",
            "version": "1",
            "stage": "stable",
            "family": family,
            "sha256": f"{phase}-{family}",
        }
        connection.execute(artefacts.insert().values(**values))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(artefacts.insert().values(**values))


def test_round_trip_preserves_data_and_supports_legacy_enum_bindings(
    migration_context: tuple[Engine, Config],
) -> None:
    engine, config = migration_context
    metadata = MetaData()
    artefacts = Base.metadata.tables["artefact"].to_metadata(metadata)
    matching_rules = Base.metadata.tables["artefact_matching_rule"].to_metadata(metadata)
    attachment_rules = Base.metadata.tables["issue_test_result_attachment_rule"].to_metadata(metadata)
    issues = Base.metadata.tables["issue"]
    # Keep the enum bind/result processors used by pre-migration application instances.
    legacy_enum = Enum(*LEGACY_FAMILIES, name="familyname")
    artefacts.c.family.type = legacy_enum
    matching_rules.c.family.type = legacy_enum
    attachment_rules.c.families.type = ARRAY(legacy_enum)

    with engine.begin() as connection:
        set_connection_audit_context(connection, automation_name="family-migration")
        artefact_id = connection.scalar(
            artefacts.insert()
            .values(name="before", version="1", stage="stable", family="snap")
            .returning(artefacts.c.id)
        )
        matching_rule_id = connection.scalar(
            matching_rules.insert().values(family="snap").returning(matching_rules.c.id)
        )
        issue_id = connection.scalar(
            issues.insert()
            .values(source=IssueSource.GITHUB, project="test", key="1", title="test")
            .returning(issues.c.id)
        )
        connection.execute(
            attachment_rules.insert(),
            [
                {"issue_id": issue_id, "families": ["snap", "deb"]},
                {"issue_id": issue_id, "families": []},
            ],
        )

    command.upgrade(config, TARGET_REV)

    with engine.begin() as connection:
        set_connection_audit_context(connection, automation_name="family-migration")
        assert (
            connection.scalar(
                select(artefacts.c.family).where(artefacts.c.id == artefact_id, artefacts.c.family.in_(LEGACY_FAMILIES))
            )
            == "snap"
        )
        assert connection.scalar(select(matching_rules.c.family)) == "snap"
        assert connection.scalars(select(attachment_rules.c.families).order_by(attachment_rules.c.id)).all() == [
            ["snap", "deb"],
            [],
        ]
        assert (
            connection.scalar(select(attachment_rules.c.id).where(attachment_rules.c.families.any("snap"))) is not None
        )
        assert (
            connection.scalar(text("SELECT family FROM artefact_audit WHERE id = :id"), {"id": artefact_id}) == "snap"
        )

        connection.execute(artefacts.update().where(artefacts.c.id == artefact_id).values(family="deb"))
        connection.execute(matching_rules.update().where(matching_rules.c.id == matching_rule_id).values(family="deb"))
        connection.execute(
            attachment_rules.update().where(attachment_rules.c.families.any("snap")).values(families=["charm"])
        )
        connection.execute(attachment_rules.insert().values(issue_id=issue_id, families=["image"]))
        _assert_unique_indexes(connection, artefacts, "upgraded")

    command.downgrade(config, PREVIOUS_REV)

    with engine.begin() as connection:
        set_connection_audit_context(connection, automation_name="family-migration")
        assert connection.scalar(select(artefacts.c.family).where(artefacts.c.id == artefact_id)) == "deb"
        assert connection.scalar(select(matching_rules.c.family)) == "deb"
        assert connection.scalars(select(attachment_rules.c.families).order_by(attachment_rules.c.id)).all() == [
            ["charm"],
            [],
            ["image"],
        ]
        assert connection.scalars(
            text("SELECT family::text FROM artefact_audit WHERE id = :id ORDER BY audit_pk"),
            {"id": artefact_id},
        ).all() == ["snap", "deb"]
        _assert_unique_indexes(connection, artefacts, "downgraded")


def test_downgrade_refuses_families_outside_enum(migration_context: tuple[Engine, Config]) -> None:
    engine, config = migration_context
    command.upgrade(config, TARGET_REV)
    with engine.begin() as connection:
        set_connection_audit_context(connection, automation_name="family-migration")
        connection.execute(Base.metadata.tables["family"].insert().values(name="custom-family"))
        connection.execute(Base.metadata.tables["artefact_matching_rule"].insert().values(family="custom-family"))

    with pytest.raises(RuntimeError, match="custom-family"):
        command.downgrade(config, PREVIOUS_REV)

    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == TARGET_REV
        assert connection.scalar(text("SELECT family FROM artefact_matching_rule")) == "custom-family"
