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

from datetime import datetime

from fastapi import Depends, Request
from sqlalchemy.orm import Session, selectinload

from test_observer.data_access.models import User, UserSession
from test_observer.data_access.setup import get_db


def get_user_session(request: Request, db: Session = Depends(get_db)) -> UserSession | None:
    # This is a protection against CSRF see "Disallowing simple requests" under
    # https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
    if "X-CSRF-Token" not in request.headers:
        return None

    session_id = request.session.get("id")
    if not session_id:
        return None

    session = db.get(UserSession, session_id, options=[selectinload(UserSession.user)])
    if not session or session.expires_at < datetime.now():
        return None

    return session


def get_current_user(
    session: UserSession | None = Depends(get_user_session),
) -> User | None:
    if session:
        return session.user
    return None
