# Copyright (C) 2026 Canonical Ltd.
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

from test_observer.common.metrics import (
    test_executions_results,
    test_executions_results_metadata_charm_cli,
    test_executions_results_metadata_simple,
    test_execution_results_metadata_charm_revision,
    test_execution_results_metadata_charm_failure,
)
from test_observer.common.metrics_helpers import get_common_metric_labels
from test_observer.controllers.test_executions.models import TestResultRequest
from test_observer.controllers.execution_metadata.models import ExecutionMetadata
from test_observer.data_access.models import (
    TestExecution,
    TestCase,
)


def update_test_execution_results_metric(
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


def update_cli_metadata_metric(
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


def update_execution_metadata_metrics(
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
