# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3, as
# published by the Free Software Foundation.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the License along with this program.  If
# not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from test_observer.data_access.audit import set_audit_context
from test_observer.data_access.models import Artefact
from test_observer.data_access.models_enums import FamilyName
from tests.data_generator import DataGenerator


def test_set_audit_context_merges_actors_and_reapplies_after_commit(db_session: Session) -> None:
    set_audit_context(db_session, user_id=12)
    set_audit_context(db_session, application_id=3)

    expected = {"automation": "tests", "user": {"id": 12}, "application": {"id": 3}}
    assert db_session.info["triggered_by"] == expected
    assert db_session.scalar(text("SELECT current_setting('audit.triggered_by')::jsonb")) == expected

    db_session.commit()

    assert db_session.scalar(text("SELECT current_setting('audit.triggered_by')::jsonb")) == expected


def test_set_audit_context_requires_an_actor(db_session: Session) -> None:
    with pytest.raises(ValueError):
        set_audit_context(db_session)
    with pytest.raises(ValueError):
        set_audit_context(db_session, automation="")
    with pytest.raises(ValueError):
        set_audit_context(db_session, automation="  ")


def test_artefact_changes_are_audited_with_context(db_session: Session) -> None:
    set_audit_context(db_session, user_id=12)
    artefact = DataGenerator(db_session).gen_artefact(name="audit-test-artefact")

    artefact.comment = "reviewed"
    db_session.commit()
    db_session.delete(artefact)
    db_session.commit()

    history = db_session.execute(
        text("SELECT audit_operation, audit_triggered_by FROM artefact_audit WHERE id = :id ORDER BY audit_pk"),
        {"id": artefact.id},
    ).all()
    assert [row.audit_operation for row in history] == ["I", "U", "D"]
    assert all(row.audit_triggered_by == {"automation": "tests", "user": {"id": 12}} for row in history)


def test_environment_review_changes_are_audited(db_session: Session) -> None:
    generator = DataGenerator(db_session)
    artefact = generator.gen_artefact(name="audit-review-artefact")
    build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    review = generator.gen_artefact_build_environment_review(build, environment)

    review.review_comment = "reviewed"
    db_session.commit()
    db_session.delete(review)
    db_session.commit()

    history = db_session.execute(
        text(
            "SELECT audit_operation, audit_triggered_by "
            "FROM artefact_build_environment_review_audit WHERE id = :id ORDER BY audit_pk"
        ),
        {"id": review.id},
    ).all()
    assert [row.audit_operation for row in history] == ["I", "U", "D"]
    assert all(row.audit_triggered_by == {"automation": "tests"} for row in history)


def test_cascading_artefact_delete_is_audited_for_environment_review(db_session: Session) -> None:
    generator = DataGenerator(db_session)
    artefact = generator.gen_artefact(name="audit-cascade-artefact")
    build = generator.gen_artefact_build(artefact)
    environment = generator.gen_environment()
    review = generator.gen_artefact_build_environment_review(build, environment)
    review_id = review.id

    db_session.delete(artefact)
    db_session.commit()

    history = db_session.execute(
        text(
            "SELECT audit_operation, audit_triggered_by "
            "FROM artefact_build_environment_review_audit WHERE id = :id ORDER BY audit_pk"
        ),
        {"id": review_id},
    ).all()
    assert [row.audit_operation for row in history] == ["I", "D"]
    assert all(row.audit_triggered_by == {"automation": "tests"} for row in history)


def test_audited_write_without_context_fails(db_session: Session) -> None:
    db_session.info.pop("triggered_by")
    db_session.execute(text("SELECT set_config('audit.triggered_by', '', true)"))

    db_session.add(
        Artefact(
            name="missing-audit-context",
            version="1",
            stage="beta",
            family=FamilyName.snap,
        )
    )
    with pytest.raises(SQLAlchemyError):
        db_session.flush()
