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

from enum import StrEnum, auto

from fastapi import Depends, HTTPException
from fastapi.security import SecurityScopes

from test_observer.common.config import IGNORE_PERMISSIONS
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.data_access.models import Application, User
from test_observer.users.user_injection import get_current_user


class Permission(StrEnum):
    # Authentication
    view_user = auto()
    change_user = auto()
    view_team = auto()
    change_team = auto()
    add_application = auto()
    change_application = auto()
    view_application = auto()
    view_permission = auto()

    # Issues
    view_issue = auto()
    change_issue = auto()
    change_issue_attachment = auto()
    change_issue_attachment_bulk = auto()
    change_attachment_rule = auto()
    change_auto_rerun = auto()

    # Tests
    view_test = auto()
    change_test = auto()
    view_rerun = auto()
    change_rerun = auto()
    change_rerun_bulk = auto()

    # Artefacts
    view_artefact = auto()
    change_artefact = auto()

    # Environment reviews
    view_environment_review = auto()
    change_environment_review = auto()

    # Reports
    view_report = auto()

    # Test cases
    view_test_case_reported_issue = auto()
    change_test_case_reported_issue = auto()

    # Environments
    view_environment_reported_issue = auto()
    change_environment_reported_issue = auto()


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
