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

from fastapi import Depends, HTTPException
from fastapi.security import SecurityScopes

from test_observer.common.config import IGNORE_PERMISSIONS
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.data_access.models import Application, User
from test_observer.users.user_injection import get_current_user


def authentication_checker(
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
) -> None:
    """
    A simple dependency to check if the request is authenticated with either a user or an application.
    This is used for endpoints that don't require specific permissions, but still require authentication.
    """
    if not user and not app:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return None


def permission_checker(
    security_scopes: SecurityScopes,
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
) -> None:
    if user and user.is_admin:
        return None

    required_permissions: set[str] = set(security_scopes.scopes) - IGNORE_PERMISSIONS

    client_permissions: set[str] = set()
    if user:
        client_permissions = {p for t in user.teams for p in t.permissions}
    if app:
        client_permissions = client_permissions.union(app.permissions)

    if not required_permissions <= client_permissions:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
