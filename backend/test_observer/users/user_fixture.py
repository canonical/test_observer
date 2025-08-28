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


from datetime import datetime
from fastapi import Depends, Request
from sqlalchemy.orm import Session, selectinload

from test_observer.data_access.models import User, UserSession
from test_observer.data_access.setup import get_db


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    session_id = request.session.get("id")
    if not session_id:
        return None

    session = db.get(UserSession, session_id, options=[selectinload(UserSession.user)])
    if not session or session.expires_at < datetime.now():
        return None

    return session.user
