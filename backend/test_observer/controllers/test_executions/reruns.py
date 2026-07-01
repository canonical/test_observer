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

import contextlib
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Response, Security, status
from fastapi.security import SecurityScopes
from sqlalchemy import Select, and_, asc, delete, desc, literal, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session, selectinload

from test_observer.common.enums import Permission
from test_observer.common.permissions import (
    has_amr_permissions,
    has_general_permission,
    openapi_scope_declaration,
    permission_checker,
)
from test_observer.controllers.applications.application_injection import (
    get_current_application,
)
from test_observer.controllers.test_executions.execution_filters import (
    apply_te_joins,
    build_execution_filters,
)
from test_observer.controllers.test_results.filter_test_results import (
    filter_test_results,
)
from test_observer.data_access.models import (
    Application,
    Artefact,
    ArtefactBuild,
    Environment,
    FamilyName,
    TestExecution,
    TestExecutionRerunRequest,
    TestResult,
    User,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db
from test_observer.users.user_injection import get_current_user

from .models import DeleteReruns, PendingRerun, RerunRequest
from .router import router


class _TestExecutionNotFound(ValueError): ...


# ==============================================================================
# DB helpers
# ==============================================================================


def _build_rerun_conditions(request: RerunRequest | DeleteReruns) -> list:
    """Return SQLAlchemy WHERE conditions identifying the affected TestExecutions.

    Raises HTTPException(422) if test_results_filters or test_executions_filters is provided but empty.
    Returns an empty list if neither criterion is provided (caller should no-op).
    """
    conditions = []

    if request.test_execution_ids:
        conditions.append(TestExecution.id.in_(request.test_execution_ids))

    if request.test_results_filters is not None:
        filters = request.test_results_filters
        if not filters.has_filters():
            raise HTTPException(
                status_code=422,
                detail="At least one filter must be provided in test_results_filters",
            )
        filtered_ids_query = filter_test_results(select(TestResult.test_execution_id).distinct(), filters)
        conditions.append(TestExecution.id.in_(filtered_ids_query))

    if request.test_executions_filters is not None:
        te_filters = request.test_executions_filters
        query_filters, joins_needed = build_execution_filters(te_filters)
        if not query_filters and not joins_needed:
            raise HTTPException(
                status_code=422,
                detail="At least one filter must be provided in test_executions_filters",
            )
        filtered_ids_query = apply_te_joins(select(TestExecution.id).distinct(), joins_needed)
        if query_filters:
            filtered_ids_query = filtered_ids_query.where(and_(*query_filters))
        conditions.append(TestExecution.id.in_(filtered_ids_query))

    return conditions


def _rerun_group_subquery(conditions: list) -> Select[tuple[int, int, int]]:
    """Select the composite key (test_plan_id, artefact_build_id, environment_id) for matching executions."""
    return (
        select(
            TestExecution.test_plan_id,
            TestExecution.artefact_build_id,
            TestExecution.environment_id,
        )
        .where(or_(*conditions))
        .distinct()
    )


def _create_reruns(db: Session, conditions: list, priority: int | None) -> None:
    subquery = _rerun_group_subquery(conditions)
    if priority is not None:
        subquery = subquery.add_columns(literal(priority).label("priority"))
        insert_stmt = pg_insert(TestExecutionRerunRequest).from_select(
            ["test_plan_id", "artefact_build_id", "environment_id", "priority"],
            subquery,
        )
        db.execute(
            insert_stmt.on_conflict_do_update(
                constraint="uq_rerun_request_group",
                set_={"priority": insert_stmt.excluded.priority},
            )
        )
    else:
        insert_stmt = pg_insert(TestExecutionRerunRequest).from_select(
            ["test_plan_id", "artefact_build_id", "environment_id"],
            subquery,
        )
        db.execute(insert_stmt.on_conflict_do_nothing())


def _delete_reruns(db: Session, conditions: list) -> None:
    subquery = _rerun_group_subquery(conditions)
    db.execute(
        delete(TestExecutionRerunRequest).where(
            tuple_(
                TestExecutionRerunRequest.test_plan_id,
                TestExecutionRerunRequest.artefact_build_id,
                TestExecutionRerunRequest.environment_id,
            ).in_(subquery)
        )
    )


def _create_rerun_request(
    test_execution_id: int, db: Session, priority: int | None = None
) -> TestExecutionRerunRequest:
    te = db.get(TestExecution, test_execution_id)
    if not te:
        raise _TestExecutionNotFound

    rerun = get_or_create(
        db,
        TestExecutionRerunRequest,
        {
            "test_plan_id": te.test_plan_id,
            "artefact_build_id": te.artefact_build_id,
            "environment_id": te.environment_id,
        },
        creation_kwargs={"priority": priority} if priority is not None else None,
    )
    # If the record already existed, get_or_create ignores creation_kwargs,
    # so explicitly update priority here.
    if priority is not None:
        rerun.priority = priority
    return rerun


# ==============================================================================
# Permission helpers (FastAPI dependencies)
# ==============================================================================


def require_bulk_permission(
    request: RerunRequest | DeleteReruns,
    security_scopes: SecurityScopes,
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
):
    if (
        len(request.test_execution_ids) > 1
        or request.test_results_filters is not None
        or request.test_executions_filters is not None
    ):
        permission_checker(security_scopes, user, app)


def _validate_amr_permissions(
    db: Session,
    user: User | None,
    app: Application | None,
    request: RerunRequest | DeleteReruns,
    permission: Permission,
) -> None:
    """Raise HTTPException(403) if the user/app lacks AMR permission on any affected artefact."""
    if has_general_permission(user, app, permission):
        return

    if user is None:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    conditions = _build_rerun_conditions(request)
    if not conditions:
        return

    affected_artefacts_query = (
        select(Artefact)
        .distinct()
        .join(ArtefactBuild, Artefact.id == ArtefactBuild.artefact_id)
        .join(TestExecution, TestExecution.artefact_build_id == ArtefactBuild.id)
        .where(or_(*conditions))
    )
    affected_artefacts = db.scalars(affected_artefacts_query).all()
    if not has_amr_permissions(db, user, affected_artefacts, permission):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


# ==============================================================================
# Route handlers
# ==============================================================================


@router.post(
    "/reruns",
    response_model=list[PendingRerun] | None,
    dependencies=[
        Security(openapi_scope_declaration, scopes=[Permission.change_rerun]),
        Security(require_bulk_permission, scopes=[Permission.change_rerun_bulk]),
    ],
)
def create_rerun_requests(
    request: RerunRequest,
    response: Response,
    silent: Annotated[
        bool,
        Query(
            description=(
                "If true, omit returning created reruns in the response body. "
                "Speeds up bulk operations, as the rerun schema contains a lot of "
                "information and returning many reruns can be slow. "
                "Required when creating reruns with test result filters."
            ),
        ),
    ] = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
):
    _validate_amr_permissions(db, user, app, request, Permission.change_rerun)

    if silent:
        conditions = _build_rerun_conditions(request)
        if conditions:
            _create_reruns(db, conditions, request.priority)
            db.commit()
        return

    if request.test_results_filters is not None or request.test_executions_filters is not None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Creating rerun requests from filters must be done silently",
        )

    rerun_requests = []
    for test_execution_id in request.test_execution_ids:
        with contextlib.suppress(_TestExecutionNotFound):
            rerun_requests.append(_create_rerun_request(test_execution_id, db, request.priority))

    if not rerun_requests:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Didn't find test executions with provided ids",
        )

    if len(rerun_requests) != len(request.test_execution_ids):
        response.status_code = status.HTTP_207_MULTI_STATUS

    db.commit()

    return rerun_requests


@router.get(
    "/reruns",
    response_model=list[PendingRerun],
    dependencies=[Security(permission_checker, scopes=[Permission.view_rerun])],
)
def get_rerun_requests(
    family: FamilyName | None = None,
    limit: int | None = None,
    environment: str | None = None,
    environment_architecture: str | None = None,
    build_architecture: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = (
        select(TestExecutionRerunRequest)
        .join(TestExecutionRerunRequest.artefact_build)
        .join(ArtefactBuild.artefact)
        .join(TestExecutionRerunRequest.environment)
        .options(
            selectinload(TestExecutionRerunRequest.artefact_build)
            .selectinload(ArtefactBuild.artefact)
            .selectinload(Artefact.reviewers),
            selectinload(TestExecutionRerunRequest.environment),
            selectinload(TestExecutionRerunRequest.test_plan),
            selectinload(TestExecutionRerunRequest.test_executions),
        )
        .order_by(
            desc(TestExecutionRerunRequest.priority),
            asc(TestExecutionRerunRequest.created_at),
            asc(TestExecutionRerunRequest.id),
        )
    )

    if family is not None:
        stmt = stmt.filter(Artefact.family == family)

    if environment is not None:
        stmt = stmt.filter(Environment.name == environment)

    if build_architecture is not None:
        stmt = stmt.filter(ArtefactBuild.architecture == build_architecture)

    if environment_architecture is not None:
        stmt = stmt.filter(Environment.architecture == environment_architecture)

    if limit is not None:
        stmt = stmt.limit(limit)

    return db.scalars(stmt)


@router.delete(
    "/reruns",
    dependencies=[
        Security(openapi_scope_declaration, scopes=[Permission.change_rerun]),
        Security(require_bulk_permission, scopes=[Permission.change_rerun_bulk]),
    ],
)
def delete_rerun_requests(
    request: DeleteReruns,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user),
    app: Application | None = Depends(get_current_application),
):
    _validate_amr_permissions(db, user, app, request, Permission.change_rerun)

    conditions = _build_rerun_conditions(request)
    if conditions:
        _delete_reruns(db, conditions)
        db.commit()
