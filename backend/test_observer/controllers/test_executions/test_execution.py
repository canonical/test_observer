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


from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.common.metrics import (
    test_executions_results_metadata_simple,
    test_execution_results_metadata_charm_revision,
    test_execution_results_metadata_charm_failure,
)
from test_observer.controllers.artefacts.models import TestExecutionResponse
from test_observer.data_access.models import TestExecution
from test_observer.data_access.models_enums import TestExecutionStatus, TestResultStatus
from test_observer.data_access.setup import get_db

from .models import TestExecutionsPatchRequest

from sqlalchemy import tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert

from test_observer.data_access.models import (
    ArtefactBuild,
    TestExecutionMetadata,
    test_execution_metadata_association_table,
)
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.common.metrics_helpers import get_common_metric_labels

router = APIRouter()


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
        options=[selectinload(TestExecution.relevant_links)],
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
        options=[
            selectinload(TestExecution.relevant_links),
            selectinload(TestExecution.artefact_build).selectinload(
                ArtefactBuild.artefact
            ),
            selectinload(TestExecution.execution_metadata),
            selectinload(TestExecution.test_results),
            selectinload(TestExecution.test_plan),
        ],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    if request.c3_link is not None:
        test_execution.c3_link = str(request.c3_link)

    if request.ci_link is not None:
        test_execution.ci_link = str(request.ci_link)

    if request.execution_metadata is not None:
        _add_execution_metadata(test_execution, request.execution_metadata, db)
        _update_execution_metadata_metrics(test_execution, request.execution_metadata)

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


def _update_execution_metadata_metrics(
    test_execution: TestExecution,
    execution_metadata: ExecutionMetadata,
) -> None:
    """Update Prometheus metrics for execution metadata."""
    artefact_family = test_execution.artefact_build.artefact.family

    # Only process metrics for charm family
    if artefact_family not in {"charm"}:
        return

    common_labels = get_common_metric_labels(test_execution)
    execution_metadata_rows = execution_metadata.to_rows()

    for test_result in test_execution.test_results:
        for metadata_row in execution_metadata_rows:
            # Update simple metadata metric
            test_executions_results_metadata_simple.labels(
                **common_labels,
                test_name=test_result.test_case.name,
                status=test_result.status.value,
                metadata_key=metadata_row.category,
                metadata_value=metadata_row.value,
            ).inc()

            # Update charm revision metric if pattern matches
            # Pattern: charm_qa:charm:CHARM_NAME:revision
            category = metadata_row.category
            is_revision = category.startswith("charm_qa:charm:") and category.endswith(
                ":revision"
            )
            if is_revision:
                parts = category.split(":")
                if len(parts) == 4:
                    charm_name = parts[2]
                    charm_revision = metadata_row.value
                    test_execution_results_metadata_charm_revision.labels(
                        **common_labels,
                        test_name=test_result.test_case.name,
                        status=test_result.status.value,
                        charm_name=charm_name,
                        charm_revision=charm_revision,
                    ).inc()

            # Update charm failure metric if pattern matches
            # Pattern: charm_qa:failure:charm:CHARM_NAME:status
            # Value format: entity_type:charm_status:status_message
            is_failure = category.startswith(
                "charm_qa:failure:charm:"
            ) and category.endswith(":status")
            if is_failure:
                parts = category.split(":")
                if len(parts) == 5:
                    charm_name = parts[3]
                    value_str = metadata_row.value
                    value_parts = value_str.split(":", 2)
                    if len(value_parts) >= 2:
                        entity_type = value_parts[0]
                        charm_status = value_parts[1]
                        status_message = value_parts[2] if len(value_parts) > 2 else ""
                        test_execution_results_metadata_charm_failure.labels(
                            **common_labels,
                            test_name=test_result.test_case.name,
                            status=test_result.status.value,
                            charm_name=charm_name,
                            entity_type=entity_type,
                            charm_status=charm_status,
                            status_message=status_message,
                        ).inc()
