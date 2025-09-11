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


from enum import StrEnum, auto


from fastapi import Depends, HTTPException
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.data_access.models import Application, User
from test_observer.users.user_injection import get_current_user


def require_permissions(*required_permissions: str):
    def permission_checker(
        user: User | None = Depends(get_current_user),
        app: Application | None = Depends(get_current_application),
    ) -> None:
        if user and user.is_admin:
            return None

        client_permissions: set[str] = set()
        if user:
            client_permissions = {p for t in user.teams for p in t.permissions}
        if app:
            client_permissions = client_permissions.union(app.permissions)

        if not all(p in client_permissions for p in required_permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    return permission_checker


class Permission(StrEnum):
    view_user = auto()
    change_user = auto()
    view_team = auto()
    change_team = auto()
    add_application = auto()
    change_application = auto()
    view_application = auto()
