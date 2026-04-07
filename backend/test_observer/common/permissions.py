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
from sqlalchemy.orm import Session, selectinload

from test_observer.common.config import IGNORE_PERMISSIONS
from test_observer.common.enums import Permission
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.data_access.models import Application, Artefact, User
from test_observer.data_access.queries import match_artefact
from test_observer.users.user_injection import get_current_user


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


def check_amr_permission(
    db: Session,
    user: User | None,
    artefact: Artefact,
    required_permission: Permission,
) -> None:
    """
    Check if a user has the required permission for an artefact based on AMR matching.

    Uses the match_artefact query to find the best-matching AMR(s) for the artefact,
    then checks if the user is in one of the teams associated with those AMRs and
    if the AMR grants the required permission.

    Args:
        db: Database session
        user: Current user (can be None)
        artefact: Artefact being accessed
        required_permission: Permission to check for

    Raises:
        HTTPException(403): If user is not authorized
    """
    if user is None:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    if user.is_admin:
        return None

    # Query for matching AMR IDs using the centralized matching logic
    matching_amr_ids = db.execute(match_artefact(artefact)).scalars().all()

    if not matching_amr_ids:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    # Load the full AMR objects with their teams and permissions
    from test_observer.data_access.models import ArtefactMatchingRule

    matching_rules = (
        db.query(ArtefactMatchingRule)
        .filter(ArtefactMatchingRule.id.in_(matching_amr_ids))
        .options(selectinload(ArtefactMatchingRule.teams))
        .all()
    )

    # Check if user is in any of the teams from matching AMRs
    # and if those AMRs grant the required permission
    user_team_ids = {team.id for team in user.teams}

    for rule in matching_rules:
        rule_team_ids = {team.id for team in rule.teams}

        user_in_rule_team = user_team_ids & rule_team_ids
        rule_grants_permission = required_permission in rule.grant_permissions
        if user_in_rule_team and rule_grants_permission:
            return None

    # If we get here, user doesn't have permission
    raise HTTPException(status_code=403, detail="Insufficient permissions")
