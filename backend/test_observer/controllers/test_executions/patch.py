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


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from test_observer.controllers.artefacts.models import TestExecutionResponse
from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.setup import get_db

from .models import TestExecutionsPatchRequest

from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_observer.data_access.models import (
    TestExecutionMetadata,
    test_execution_metadata_association_table,
)
from test_observer.controllers.execution_metadata.models import ExecutionMetadata

router = APIRouter()


@router.patch("/{id}", response_model=TestExecutionResponse)
def patch_test_execution(
    id: int,
    request: TestExecutionsPatchRequest,
    db: Session = Depends(get_db),
):
    test_execution = db.get(
        TestExecution,
        id,
        options=[selectinload(TestExecution.relevant_links)],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    if request.c3_link is not None:
        test_execution.c3_link = str(request.c3_link)

    if request.ci_link is not None:
        test_execution.ci_link = str(request.ci_link)

    if request.execution_metadata is not None:
        _add_execution_metadata(test_execution, request.execution_metadata, db)

    _set_test_execution_status(request, test_execution)

    db.commit()
    db.refresh(test_execution)
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
