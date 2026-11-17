# Copyright 2026 Canonical Ltd.
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
# SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
# SPDX-License-Identifier: AGPL-3.0-only

from fastapi.testclient import TestClient
from prometheus_client import REGISTRY
from sqlalchemy.orm import Session

from test_observer.common.enums import Permission
from test_observer.common.metric_collectors import _get_base_metric_labels
from test_observer.common.metrics_initializer import (
    _initialize_metadata_metrics,
    _initialize_test_results_metric,
    _initialize_triaged_metrics,
)
from test_observer.data_access.models import IssueTestResultAttachment
from test_observer.data_access.models_enums import FamilyName
from tests.conftest import make_authenticated_request
from tests.data_generator import DataGenerator


def auth_post(test_client: TestClient, endpoint: str, json: dict):
    return make_authenticated_request(
        lambda: test_client.post(endpoint, json=json),
        Permission.change_issue_attachment,
    )


def get_metric_value(metric_name: str, labels: dict) -> float:
    """Get the current value of a Prometheus metric with specific labels."""
    for metric in REGISTRY.collect():
        if metric.name == metric_name:
            for sample in metric.samples:
                if sample.name == metric_name and all(sample.labels.get(k) == v for k, v in labels.items()):
                    return sample.value
    return 0.0


def test_metrics_support_string_families(generator: DataGenerator, db_session: Session) -> None:
    artefact = generator.gen_artefact(name="metric-string-family")
    execution = generator.gen_test_execution(
        generator.gen_artefact_build(artefact),
        generator.gen_environment(),
        execution_metadata={"category": ["value"]},
    )
    result = generator.gen_test_result(generator.gen_test_case(), execution)
    issue = generator.gen_issue()
    db_session.add(IssueTestResultAttachment(issue=issue, test_result=result))
    db_session.commit()
    db_session.refresh(artefact)

    assert _get_base_metric_labels(execution)["family"] == "snap"
    assert _initialize_test_results_metric(db_session) == 1
    assert _initialize_triaged_metrics(db_session) == 1
    assert _initialize_metadata_metrics(db_session) == 1


def test_triaged_metric_incremented_on_attach(test_client: TestClient, generator: DataGenerator):
    """
    Test that the triaged metric is incremented when an issue is attached
    to a test result.
    """
    # Generate test data for charm family
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact(
        name="test-charm",
        family=FamilyName.charm,
        track="latest",
        stage="edge",
    )
    artefact_build = generator.gen_artefact_build(artefact)
    test_plan_name = "integration/provider:endpoint1/interface1/requirer:endpoint2"
    generator.gen_test_plan(name=test_plan_name)
    test_execution = generator.gen_test_execution(artefact_build, environment, test_plan=test_plan_name)
    test_result = generator.gen_test_result(test_case, test_execution)
    issue = generator.gen_issue()

    # Get initial metric value
    metric_labels = {
        "family": artefact.family,
        "artefact_name": artefact.name,
        "artefact_stage": artefact.stage,
        "track": artefact.track or "",
        "series": artefact.series or "",
        "os": artefact.os or "",
        "environment_name": environment.name,
        "test_plan": test_plan_name,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "issue_source": issue.source.value,
        "issue_project": issue.project,
        "issue_key": issue.key,
    }
    initial_value = get_metric_value("test_observer_test_results_triaged", metric_labels)

    # Attach the issue
    response = auth_post(
        test_client,
        f"/v1/issues/{issue.id}/attach",
        {"test_results": [test_result.id]},
    )
    assert response.status_code == 200

    # Verify metric was incremented
    new_value = get_metric_value("test_observer_test_results_triaged", metric_labels)
    assert new_value == initial_value + 1


def test_triaged_metric_decremented_on_detach(test_client: TestClient, generator: DataGenerator):
    """
    Test that the triaged metric is decremented when an issue is detached
    from a test result.
    """
    # Generate test data for charm family
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact(
        name="test-charm",
        family=FamilyName.charm,
        track="latest",
        stage="edge",
    )
    artefact_build = generator.gen_artefact_build(artefact)
    test_plan_name = "integration/provider:endpoint1/interface1/requirer:endpoint2"
    generator.gen_test_plan(name=test_plan_name)
    test_execution = generator.gen_test_execution(artefact_build, environment, test_plan=test_plan_name)
    test_result = generator.gen_test_result(test_case, test_execution)
    issue = generator.gen_issue()

    # Attach the issue first
    response = auth_post(
        test_client,
        f"/v1/issues/{issue.id}/attach",
        {"test_results": [test_result.id]},
    )
    assert response.status_code == 200

    # Get metric value after attach
    metric_labels = {
        "family": artefact.family,
        "artefact_name": artefact.name,
        "artefact_stage": artefact.stage,
        "track": artefact.track or "",
        "series": artefact.series or "",
        "os": artefact.os or "",
        "environment_name": environment.name,
        "test_plan": test_plan_name,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "issue_source": issue.source.value,
        "issue_project": issue.project,
        "issue_key": issue.key,
    }
    value_after_attach = get_metric_value("test_observer_test_results_triaged", metric_labels)

    # Detach the issue
    response = auth_post(
        test_client,
        f"/v1/issues/{issue.id}/detach",
        {"test_results": [test_result.id]},
    )
    assert response.status_code == 200

    # Verify metric was decremented
    new_value = get_metric_value("test_observer_test_results_triaged", metric_labels)
    assert new_value == value_after_attach - 1


def test_triaged_metric_not_updated_for_non_charm_family(test_client: TestClient, generator: DataGenerator):
    """Test that the triaged metric is not updated for non-charm families."""
    # Generate test data for snap family
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact(name="test-snap", family=FamilyName.snap, track="latest", stage="edge")
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    test_result = generator.gen_test_result(test_case, test_execution)
    issue = generator.gen_issue()

    # Attach the issue
    response = auth_post(
        test_client,
        f"/v1/issues/{issue.id}/attach",
        {"test_results": [test_result.id]},
    )
    assert response.status_code == 200

    # Issue should be attached
    assert len(issue.test_result_attachments) == 1

    # But metric should not exist for snap family (would require different labels)
    # This test just verifies no exception is raised for non-charm families
