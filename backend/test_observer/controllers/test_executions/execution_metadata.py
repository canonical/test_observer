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
from sqlalchemy import tuple_
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_observer.data_access.models import (
    TestExecution,
    TestExecutionMetadata,
    test_execution_metadata_association_table,
)
from test_observer.data_access.setup import get_db
from test_observer.controllers.execution_metadata.models import (
    ExecutionMetadataGetResponse,
    ExecutionMetadataPostRequest,
    ExecutionMetadata,
)


router = APIRouter(tags=["execution-metadata"])


@router.get(
    "/{test_execution_id}/execution-metadata",
    response_model=ExecutionMetadataGetResponse,
)
def get_execution_metadata(test_execution_id: int, db: Session = Depends(get_db)):
    test_execution = db.get(TestExecution, test_execution_id)
    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")
    return ExecutionMetadataGetResponse(
        execution_metadata=ExecutionMetadata.from_rows(
            test_execution.execution_metadata
        ),
    )


@router.post(
    "/{test_execution_id}/execution-metadata",
    response_model=ExecutionMetadataGetResponse,
)
def post_execution_metadata(
    test_execution_id: int,
    request: ExecutionMetadataPostRequest,
    db: Session = Depends(get_db),
):
    # Get the test execution
    test_execution = db.get(TestExecution, test_execution_id)
    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    # Unpack metadata into list
    execution_metadata_rows = request.execution_metadata.to_rows()

    # Exit if none given
    if len(execution_metadata_rows) == 0:
        return ExecutionMetadataGetResponse(
            execution_metadata=ExecutionMetadata.from_rows(
                test_execution.execution_metadata
            ),
        )

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
                    "test_execution_id": test_execution_id,
                    "test_execution_metadata_id": execution_metadata_id[0],
                }
                for execution_metadata_id in execution_metadata_ids
            ]
        )
        .on_conflict_do_nothing()
    )

    # Save and return all the execution metadata
    db.commit()
    db.refresh(test_execution)
    return ExecutionMetadataGetResponse(
        execution_metadata=ExecutionMetadata.from_rows(
            test_execution.execution_metadata
        ),
    )
