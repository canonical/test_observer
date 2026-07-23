# Copyright 2025 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from test_observer.data_access.models import Issue
from test_observer.data_access.models_enums import FamilyName, IssueSource, StageName
from tests.data_generator import DataGenerator


@pytest.mark.parametrize(
    "source_project_key,expected",
    [
        # Unknown source
        (("unknown_source", "some-project", "some-key"), None),
        # Github
        (
            (IssueSource.GITHUB, "canonical/test_observer", "71"),
            "https://github.com/canonical/test_observer/issues/71",
        ),
        # Jira
        (
            (IssueSource.JIRA, "TO", "142"),
            "https://warthogs.atlassian.net/browse/TO-142",
        ),
        # Launchpad
        (
            (IssueSource.LAUNCHPAD, "abc", "123"),
            "https://bugs.launchpad.net/abc/+bug/123",
        ),
    ],
)
def test_issue_url(
    source_project_key: tuple[IssueSource, str, str],
    expected: str | None,
):
    try:
        source, project, key = source_project_key
        result = Issue(source=source, project=project, key=key).url
    except ValueError:
        assert expected is None
    else:
        assert result == expected


def test_solutions_with_same_name_and_version_are_unique(generator: DataGenerator, db_session: Session) -> None:
    generator.gen_artefact(family=FamilyName.solution, name="solution", version="1.0")

    with pytest.raises(IntegrityError):
        generator.gen_artefact(family=FamilyName.solution, name="solution", version="1.0")
    db_session.rollback()


def test_solutions_with_same_name_and_different_versions_are_allowed(generator: DataGenerator) -> None:
    first = generator.gen_artefact(family=FamilyName.solution, name="solution", version="1.0")
    second = generator.gen_artefact(family=FamilyName.solution, name="solution", version="2.0")

    assert first.id != second.id


def test_solutions_with_same_version_and_different_names_are_allowed(generator: DataGenerator) -> None:
    first = generator.gen_artefact(family=FamilyName.solution, name="solution-a", version="1.0")
    second = generator.gen_artefact(family=FamilyName.solution, name="solution-b", version="1.0")

    assert first.id != second.id


def test_solutions_with_different_name_and_version_are_allowed(generator: DataGenerator) -> None:
    first = generator.gen_artefact(family=FamilyName.solution, name="solution-a", version="1.0")
    second = generator.gen_artefact(family=FamilyName.solution, name="solution-b", version="2.0")

    assert first.id != second.id


def test_solution_unique_constraint_ignores_source_track_and_stage(
    generator: DataGenerator, db_session: Session
) -> None:
    generator.gen_artefact(
        family=FamilyName.solution,
        name="solution",
        version="1.0",
        source="first-source",
        track="first-track",
        stage=StageName.beta,
    )

    with pytest.raises(IntegrityError):
        generator.gen_artefact(
            family=FamilyName.solution,
            name="solution",
            version="1.0",
            source="second-source",
            track="second-track",
            stage=StageName.stable,
        )
    db_session.rollback()


def test_snap_name_and_version_duplicates_are_not_blocked_by_solution_constraint(generator: DataGenerator) -> None:
    first = generator.gen_artefact(
        family=FamilyName.snap,
        name="core",
        version="1.0",
        track="latest",
    )
    second = generator.gen_artefact(
        family=FamilyName.snap,
        name="core",
        version="1.0",
        track="other-track",
    )

    assert first.id != second.id
