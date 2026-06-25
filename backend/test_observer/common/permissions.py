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

from test_observer.common.config import IGNORE_PERMISSIONS, REQUIRE_AUTHENTICATION
from test_observer.common.enums import Permission
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.data_access.models import Application, Artefact, ArtefactMatchingRule, User
from test_observer.data_access.queries import batch_match_artefacts
from test_observer.users.user_injection import get_current_user, get_current_user_browser_friendly


def requires_authentication() -> bool:
    """
    Simply returns the REQUIRE_AUTHENTICATION config value.
    By making this a function, it can be used as a dependency
    for routes that require authentication, and being a dependency
    in turn makes it easier to override in tests if needed.
    """
    return REQUIRE_AUTHENTICATION


def authentication_checker(
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
    authentication_required: bool = Depends(requires_authentication),
) -> None:
    """
    A simple dependency to check if the request is authenticated with either a user or an application.
    This is used for endpoints that don't require specific permissions, but still require authentication.
    """
    if authentication_required and not user and not app:
        raise HTTPException(status_code=401, detail="Not authenticated")


def authentication_checker_browser_friendly(
    user: User | None = Depends(get_current_user_browser_friendly),
    app: Application | None = Depends(get_current_application),
    authentication_required: bool = Depends(requires_authentication),
) -> None:
    """
    A browser-friendly version of the authentication checker that allows GET requests without a CSRF token
    through the underlying `get_current_user_browser_friendly` dependency.
    This must only be used for endpoints that are safe to trigger cross-site and have no side effects.

    At the time of writing, this should only be used for the /docs endpoint, as that is the only endpoint
    intended to be used directly in the browser. Other endpoints can be used in the browser _from_ the Swagger docs.
    """
    if authentication_required and not user and not app:
        raise HTTPException(status_code=401, detail="Not authenticated")


def permission_checker(
    security_scopes: SecurityScopes,
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
) -> None:
    if user and user.is_admin:
        return

    required_permissions: set[str] = set(security_scopes.scopes) - IGNORE_PERMISSIONS

    client_permissions: set[str] = set()
    if user:
        client_permissions = {p for t in user.teams for p in t.permissions}
    if app:
        client_permissions = client_permissions.union(app.permissions)

    if not required_permissions <= client_permissions:
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def has_general_permission(
    user: User | None,
    app: Application | None,
    required_permission: Permission,
    ignored_permissions: set[str] | None = None,
) -> bool:
    """
    Determine whether a user or application has the required permission.

    Args:
        user: The User to check (can be None)
        app: The Application to check (can be None)
        required_permission: Permission to check for
        ignored_permissions:
            Optional set of permissions to ignore.
            If None, defaults to IGNORE_PERMISSIONS from config.
    """
    if user and (user.is_admin or any(required_permission in t.permissions for t in user.teams)):
        return True
    if app and required_permission in app.permissions:
        return True

    if ignored_permissions is None:
        ignored_permissions = IGNORE_PERMISSIONS
    return required_permission.value in ignored_permissions


def check_general_permission(
    user: User | None,
    app: Application | None,
    required_permission: Permission,
    ignored_permissions: set[str] | None = None,
) -> None:
    """
    Centralized permission check for general operations.

    Args:
        user: The User to check (can be None)
        app: The Application to check (can be None)
        required_permission: Permission to check for
        ignored_permissions:
            Optional set of permissions to ignore.
            If None, defaults to IGNORE_PERMISSIONS from config.

    Raises:
        HTTPException(403): If user is not authorized
    """
    if not has_general_permission(user, app, required_permission, ignored_permissions):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def has_amr_permissions(
    db: Session,
    user: User | None,
    artefacts: list[Artefact],
    required_permission: Permission,
) -> bool:
    """
    Determine whether a user has the required permission for a list of artefacts based on AMR matching.

    Args:
        db: Database session
        user: Current user (can be None)
        artefacts: List of artefacts being accessed
        required_permission: Permission to check for
    """
    if not user:
        return False

    # If no affected artefacts, no permissions to check (e.g., invalid test_execution_ids)
    if not artefacts:
        return True

    batch_match_result = db.execute(batch_match_artefacts(list(artefacts))).all()

    # Build map: artefact_id → set of matching AMR IDs
    artefact_to_amrs: dict[int, set[int]] = {}
    matched_amr_ids: set[int] = set()
    for artefact_id, amr_id in batch_match_result:
        artefact_to_amrs.setdefault(artefact_id, set()).add(amr_id)
        matched_amr_ids.add(amr_id)

    # Fetch all matching AMRs with teams in a single query
    if matched_amr_ids:
        matching_rules = (
            db.query(ArtefactMatchingRule)
            .filter(ArtefactMatchingRule.id.in_(matched_amr_ids))
            .options(selectinload(ArtefactMatchingRule.teams))
            .all()
        )
    else:
        matching_rules = []

    # Build map: AMR ID → rule with teams
    amr_rules = {rule.id: rule for rule in matching_rules}

    # Check permission for each affected artefact using all-or-nothing semantics
    user_team_ids = {team.id for team in user.teams}

    for artefact in artefacts:
        matching_amr_ids = artefact_to_amrs.get(artefact.id, set())

        if not matching_amr_ids:
            # No AMRs match this artefact
            return False

        # Check if user is in a team with a matching AMR that grants the permission
        has_permission = False
        for amr_id in matching_amr_ids:
            rule = amr_rules.get(amr_id)
            if rule is not None and required_permission in rule.grant_permissions:
                rule_team_ids = {team.id for team in rule.teams}
                if user_team_ids & rule_team_ids:
                    has_permission = True
                    break

        if not has_permission:
            return False

    return True


def check_amr_permissions(
    db: Session,
    user: User | None,
    artefacts: list[Artefact],
    required_permission: Permission,
) -> None:
    """
    Centralized permission check for artefact operations based on AMR matching.
    Errors with HTTP 403 if the user does not have the required permission.
    """
    if not has_amr_permissions(db, user, artefacts, required_permission):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def check_artefact_permission(
    db: Session,
    user: User | None,
    app: Application | None,
    artefact: Artefact,
    required_permission: Permission,
    ignored_permissions: set[str] | None = None,
) -> None:
    """
    Centralized permission check for artefact operations.

    Args:
        db: Database session
        user: Current user (can be None)
        app: Current application (can be None)
        artefact: Artefact being accessed
        required_permission: Permission to check for
        ignored_permissions:
            Optional set of permissions to ignore.
            If None, defaults to IGNORE_PERMISSIONS from config.

    Raises:
        HTTPException(403): If user is not authorized
    """

    if has_general_permission(user, app, required_permission, ignored_permissions) or has_amr_permissions(
        db, user, [artefact], required_permission
    ):
        return

    raise HTTPException(status_code=403, detail="Insufficient permissions")


def openapi_scope_declaration() -> None:
    """
    No-op dependency for OpenAPI scope declaration via Security(..., scopes=[...]).

    FastAPI captures scopes at dependency registration time (startup), so this
    dependency just needs to exist. The actual scope values are provided via the
    Security(..., scopes=[...]) parameter in the route decorator, which the OpenAPI
    generator reads at startup time.

    The actual permission checking happens inside the endpoint using
    check_artefact_permission() or check_amr_permission().
    """
    pass
