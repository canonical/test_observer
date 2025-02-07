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


from sqlalchemy.orm import Session

from test_observer.data_access.models import Artefact, User
from test_observer.data_access.setup import SessionLocal


def change_assignee(
    artefact_id: int, user_id: int, session: Session | None = None
) -> Artefact:
    if session is None:
        session = SessionLocal()
        try:
            return _change_assignee(artefact_id, user_id, session)
        finally:
            session.close()
    else:
        return _change_assignee(artefact_id, user_id, session)


def _change_assignee(artefact_id: int, user_id: int, session: Session) -> Artefact:
    artefact = session.get(Artefact, artefact_id)
    user = session.get(User, user_id)

    if artefact is None:
        raise ValueError(f"No artefact with id {artefact_id} found")

    if user is None:
        raise ValueError(f"No user with id {user_id} found")

    artefact.assignee = user
    session.commit()
    return artefact
