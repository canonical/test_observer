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

from typing import TYPE_CHECKING

from test_observer.common.metrics import (
    test_results,
    test_results_triaged,
    test_results_metadata,
)

if TYPE_CHECKING:
    from test_observer.controllers.test_executions.models import TestResultRequest
    from test_observer.controllers.execution_metadata.models import ExecutionMetadata
    from test_observer.data_access.models import (
        TestExecution,
        TestCase,
        TestResult,
        Issue,
    )

from test_observer.data_access.models import TestExecution


def _get_base_metric_labels(test_execution: TestExecution) -> dict[str, str]:
    """
    Extract base metric labels from a test execution.

    Works for all families. Family-specific fields are set to empty
    string when not applicable.
    """
    artefact = test_execution.artefact_build.artefact

    return {
        "family": artefact.family.value,
        "artefact_name": artefact.name,
        "artefact_stage": artefact.stage,
        "track": artefact.track or "",
        "series": artefact.series or "",
        "os": artefact.os or "",
        "environment_name": test_execution.environment.name,
        "test_plan": test_execution.test_plan.name,
    }


def update_test_results_metric(
    test_execution: "TestExecution",
    test_case: "TestCase",
    result: "TestResultRequest",
) -> None:
    """Update basic test results metric for ALL families."""
    base_labels = _get_base_metric_labels(test_execution)

    test_results.labels(
        **base_labels,
        test_name=test_case.name,
        status=result.status.value,
    ).inc()


def update_triaged_results_metric(
    test_result: "TestResult",
    issue: "Issue",
    increment: bool = True,
) -> None:
    """Update triaged results metric for ALL families.

    Args:
        test_result: The test result to update metrics for
        issue: The issue to update metrics for
        increment: Whether to increment (True) or decrement (False) the metric
    """
    test_execution = test_result.test_execution
    base_labels = _get_base_metric_labels(test_execution)

    metric = test_results_triaged.labels(
        **base_labels,
        test_name=test_result.test_case.name,
        status=test_result.status.value,
        issue_source=issue.source.value,
        issue_project=issue.project,
        issue_key=issue.key,
    )
    if increment:
        metric.inc()
    else:
        metric.dec()


def update_execution_metadata_metric(
    test_execution: "TestExecution",
    execution_metadata: "ExecutionMetadata",
) -> None:
    """Update execution metadata metric for ALL families."""
    base_labels = _get_base_metric_labels(test_execution)
    execution_metadata_rows = execution_metadata.to_rows()

    for test_result in test_execution.test_results:
        for metadata_row in execution_metadata_rows:
            test_results_metadata.labels(
                **base_labels,
                test_name=test_result.test_case.name,
                status=test_result.status.value,
                metadata_category=metadata_row.category,
                metadata_value=metadata_row.value,
            ).inc()
