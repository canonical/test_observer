# Copyright 2024 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from sqlalchemy.orm import Session

from test_observer.data_access.models_enums import StageName
from test_observer.users.change_assignee import change_assignee
from tests.data_generator import DataGenerator


def test_change_assignee(db_session: Session, generator: DataGenerator):
    artefact = generator.gen_artefact(StageName.beta)
    user1 = generator.gen_user(
        email="user1@example.com",
        launchpad_handle="user1",
        name="User 1",
    )
    user2 = generator.gen_user(
        email="user2@example.com",
        launchpad_handle="user2",
        name="User 2",
    )
    artefact.assignee = user1
    db_session.commit()

    change_assignee(artefact.id, user2.id, db_session)

    assert artefact.assignee == user2
