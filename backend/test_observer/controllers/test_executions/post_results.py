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
from sqlalchemy import delete
from sqlalchemy.orm import Session, selectinload

from test_observer.common.permissions import Permission, permission_checker
from test_observer.common.metrics import (
    test_executions_results,
    test_executions_results_metadata_charm_cli,
)
from test_observer.common.metrics_helpers import get_common_metric_labels
from test_observer.controllers.test_executions.models import TestResultRequest
from test_observer.controllers.issues.attachment_rules_logic import (
    apply_test_result_attachment_rules,
)
from test_observer.data_access.models import (
    ArtefactBuild,
    TestCase,
    TestExecution,
    TestResult,
)
from test_observer.data_access.repository import get_or_create
from test_observer.data_access.setup import get_db

router = APIRouter(tags=["test-results"])


@router.post(
    "/{id}/test-results",
    dependencies=[Security(permission_checker, scopes=[Permission.change_test])],
)
def post_results(
    id: int,
    request: list[TestResultRequest],
    db: Session = Depends(get_db),
):
    test_execution = db.get(
        TestExecution,
        id,
        options=[
            selectinload(TestExecution.artefact_build).selectinload(
                ArtefactBuild.artefact
            ),
            selectinload(TestExecution.environment),
            selectinload(TestExecution.execution_metadata),
        ],
    )

    if test_execution is None:
        raise HTTPException(status_code=404, detail="TestExecution not found")

    for result in request:
        test_case = get_or_create(
            db,
            TestCase,
            filter_kwargs={"name": result.name},
            creation_kwargs={
                "category": result.category,
                "template_id": result.template_id,
            },
        )

        db.execute(
            delete(TestResult).where(
                TestResult.test_execution_id == test_execution.id,
                TestResult.test_case_id == test_case.id,
            )
        )

        test_result = TestResult(
            test_execution=test_execution,
            test_case=test_case,
            status=result.status,
            comment=result.comment,
            io_log=result.io_log,
        )

        db.add(test_result)
        db.flush()
        apply_test_result_attachment_rules(db, test_result)

        _update_test_execution_results_metric(test_execution, test_case, result)
        _update_cli_metadata_metric(test_execution, test_case, result)

    db.commit()


def _update_test_execution_results_metric(
    test_execution: TestExecution,
    test_case: TestCase,
    result: TestResultRequest,
) -> None:
    """Update Prometheus metric for test execution results."""
    artefact_family = test_execution.artefact_build.artefact.family

    # Only process metrics for charm family
    if artefact_family not in {"charm"}:
        return

    common_labels = get_common_metric_labels(test_execution)

    test_executions_results.labels(
        **common_labels,
        test_name=test_case.name,
        status=result.status.value,
    ).inc()


def _update_cli_metadata_metric(
    test_execution: TestExecution,
    test_case: TestCase,
    result: TestResultRequest,
) -> None:
    """Update Prometheus metric for CLI command metadata from test failures."""
    artefact_family = test_execution.artefact_build.artefact.family

    # Only process metrics for charm family
    if artefact_family not in {"charm"}:
        return

    common_labels = get_common_metric_labels(test_execution)

    # Iterate through execution metadata looking for CLI-related metadata
    for metadata in test_execution.execution_metadata:
        category = metadata.category
        value = metadata.value

        # Match pattern: charm_qa:failure:cli:cmd
        if category == "charm_qa:failure:cli:cmd":
            test_executions_results_metadata_charm_cli.labels(
                **common_labels,
                test_name=test_case.name,
                status=result.status.value,
                cmd=value,
                stderr="",
            ).inc()

        # Match pattern: charm_qa:failure:cli:stderr
        elif category == "charm_qa:failure:cli:stderr":
            test_executions_results_metadata_charm_cli.labels(
                **common_labels,
                test_name=test_case.name,
                status=result.status.value,
                cmd="",
                stderr=value,
            ).inc()
