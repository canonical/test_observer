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


"""Test services functions"""

from sqlalchemy.orm import Session

from test_observer.data_access.repository import create_test_execution_relevant_link
from tests.data_generator import DataGenerator

from pydantic import HttpUrl


def test_create_test_execution_relevant_link(
    db_session: Session, generator: DataGenerator
):
    """Test creating a relevant link for a test execution."""
    # Arrange
    artefact = generator.gen_artefact()
    artefact_build = generator.gen_artefact_build(artefact=artefact)
    environment = generator.gen_environment()

    test_execution = generator.gen_test_execution(
        artefact_build=artefact_build, environment=environment
    )

    label = "Test Link"
    url = HttpUrl("https://example.com/test-link")

    # Act
    link = create_test_execution_relevant_link(
        db_session, test_execution.id, label, url
    )

    # Assert
    assert link.label == label
    assert HttpUrl(link.url) == url
    assert link.test_execution_id == test_execution.id
    assert link.created_at is not None
    db_session.refresh(test_execution)
    assert any(rl.id == link.id for rl in test_execution.relevant_links)
