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

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy import tuple_
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_observer.common.metric_collectors import update_execution_metadata_metric
from test_observer.common.permissions import Permission, permission_checker
from test_observer.controllers.artefacts.models import TestExecutionResponse
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models import (
    TestExecution,
    TestExecutionMetadata,
    TestResult,
    test_execution_metadata_association_table,
)
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.setup import get_db

from .models import TestExecutionsPatchRequest


router = APIRouter()

TEST_EXECUTION_OPTIONS = [
    # Single-query Joins (Many-to-One)
    joinedload(TestExecution.environment),
    joinedload(TestExecution.rerun_request),
    joinedload(TestExecution.test_plan),
    # Separate-query Collections (One-to-Many / Many-to-Many)
    selectinload(TestExecution.execution_metadata),
    selectinload(TestExecution.relevant_links),
    # Used by `is_triaged` and `has_failures` methods
    selectinload(TestExecution.test_results).selectinload(TestResult.issue_attachments),
]


@router.get(
    "/{id}",
    response_model=TestExecutionResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.view_test])],
)
def get_test_execution(
    id: int,
    db: Session = Depends(get_db),
):
    test_execution = db.get(
        TestExecution,
        id,
        options=TEST_EXECUTION_OPTIONS,
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    return test_execution


@router.patch(
    "/{id}",
    response_model=TestExecutionResponse,
    dependencies=[Security(permission_checker, scopes=[Permission.change_test])],
)
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.get(
        TestExecution,
        id,
        options=TEST_EXECUTION_OPTIONS,
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    if request.c3_link is not None:
        test_execution.c3_link = str(request.c3_link)

    if request.ci_link is not None:
        test_execution.ci_link = str(request.ci_link)

    if request.execution_metadata is not None:
        _add_execution_metadata(test_execution, request.execution_metadata, db)
        update_execution_metadata_metric(test_execution, request.execution_metadata)

    _set_test_execution_status(request, test_execution)

    db.commit()

    # Because the TestExecutionResponseModel relies on relationships to other tables,
    # it is better to use another db.get(..., options=[...]) to minimize database trips
    # Because our sessionmaker uses expire_on_commit=False,
    # we need to manually expire the test_execution
    # to avoid returning stale data with db.get(..., options=[...])
    db.expire(test_execution)
    test_execution = db.get(
        TestExecution,
        id,
        options=TEST_EXECUTION_OPTIONS,
    )
    return test_execution


def _set_test_execution_status(
    request: TestExecutionsPatchRequest, test_execution: TestExecution
) -> None:
    match (request.status, test_execution.test_results):
        case (TestExecutionStatus(), _):
            test_execution.status = request.status
        case ("COMPLETED", []):
            test_execution.status = TestExecutionStatus.ENDED_PREMATURELY
        case ("COMPLETED", results) if any(
            r.status == TestResultStatus.FAILED for r in results
        ):
            test_execution.status = TestExecutionStatus.FAILED
        case ("COMPLETED", _):
            test_execution.status = TestExecutionStatus.PASSED


def _add_execution_metadata(
    test_execution: TestExecution,
    execution_metadata: ExecutionMetadata,
    db: Session,
) -> None:
    # Unpack metadata into list of tuples
    execution_metadata_rows = execution_metadata.to_rows()

    # Exit if none given
    if len(execution_metadata_rows) == 0:
        return

    # Create any missing execution metadata
    db.execute(
        pg_insert(TestExecutionMetadata)
        .values(
            [
                {
                    "category": execution_metadata.category,
                    "value": execution_metadata.value,
                }
                for execution_metadata in execution_metadata_rows
            ]
        )
        .on_conflict_do_nothing()
    )

    # Fetch all execution metadata ids
    execution_metadata_ids = (
        db.query(TestExecutionMetadata.id)
        .filter(
            tuple_(TestExecutionMetadata.category, TestExecutionMetadata.value).in_(
                [
                    (execution_metadata.category, execution_metadata.value)
                    for execution_metadata in execution_metadata_rows
                ]
            )
        )
        .all()
    )

    # Attach any missing execution metadata to the test execution
    db.execute(
        pg_insert(test_execution_metadata_association_table)
        .values(
            [
                {
                    "test_execution_id": test_execution.id,
                    "test_execution_metadata_id": execution_metadata_id[0],
                }
                for execution_metadata_id in execution_metadata_ids
            ]
        )
        .on_conflict_do_nothing()
    )
