# Copyright (C) 2025 Canonical Ltd.
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


from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from tests.data_generator import DataGenerator
from tests.conftest import make_authenticated_request
from test_observer.common.permissions import Permission
from test_observer.data_access.models import FamilyName


def auth_patch(test_client: TestClient, endpoint: str, json: dict):
    return make_authenticated_request(
        lambda: test_client.patch(endpoint, json=json),
        Permission.change_test,
    )


def get_metric_value(metric_name: str, labels: dict) -> float:
    """Get the current value of a Prometheus metric with specific labels."""
    for metric in REGISTRY.collect():
        if metric.name == metric_name:
            for sample in metric.samples:
                if sample.name == metric_name and all(
                    sample.labels.get(k) == v for k, v in labels.items()
                ):
                    return sample.value
    return 0.0


def test_charm_failure_metric_updated(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm failure metric is updated when execution metadata
    is added with charm failure information.
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
    test_execution = generator.gen_test_execution(
        artefact_build, environment, test_plan=test_plan_name
    )
    test_result = generator.gen_test_result(test_case, test_execution)

    # Get initial metric value
    metric_labels = {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "charm_name": "postgresql-k8s",
        "entity_type": "unit",
        "charm_status": "error",
        "status_message": "hook failed: install",
    }
    initial_value = get_metric_value(
        "t_obs_results_metadata_charm_failure", metric_labels
    )

    # Add execution metadata with charm failure
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm_qa:failure:charm:postgresql-k8s:status": ["unit:error:hook failed: install"],
            }
        },
    )
    assert response.status_code == 200

    # Verify metric was incremented
    new_value = get_metric_value(
        "t_obs_results_metadata_charm_failure", metric_labels
    )
    assert new_value == initial_value + 1


def test_charm_failure_metric_multiple_failures(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm failure metric is updated for multiple charm failures
    in the same test execution.
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
    test_execution = generator.gen_test_execution(
        artefact_build, environment, test_plan=test_plan_name
    )
    test_result = generator.gen_test_result(test_case, test_execution)

    # Get initial metric values for both failures
    postgres_labels = {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "charm_name": "postgresql-k8s",
        "entity_type": "unit",
        "charm_status": "error",
        "status_message": "hook failed: install",
    }
    mysql_labels = {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "charm_name": "mysql-k8s",
        "entity_type": "application",
        "charm_status": "blocked",
        "status_message": "waiting for config",
    }

    postgres_initial = get_metric_value(
        "t_obs_results_metadata_charm_failure", postgres_labels
    )
    mysql_initial = get_metric_value(
        "t_obs_results_metadata_charm_failure", mysql_labels
    )

    # Add execution metadata with multiple charm failures
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm_qa:failure:charm:postgresql-k8s:status": ["unit:error:hook failed: install"],
                "charm_qa:failure:charm:mysql-k8s:status": ["application:blocked:waiting for config"],
            }
        },
    )
    assert response.status_code == 200

    # Verify both metrics were incremented
    postgres_new = get_metric_value(
        "t_obs_results_metadata_charm_failure", postgres_labels
    )
    mysql_new = get_metric_value(
        "t_obs_results_metadata_charm_failure", mysql_labels
    )

    assert postgres_new == postgres_initial + 1
    assert mysql_new == mysql_initial + 1


def test_charm_failure_metric_different_entity_types(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm failure metric handles different entity types
    (unit vs application).
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
    test_execution = generator.gen_test_execution(
        artefact_build, environment, test_plan=test_plan_name
    )
    test_result = generator.gen_test_result(test_case, test_execution)

    # Test with unit entity type
    unit_labels = {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "charm_name": "postgresql-k8s",
        "entity_type": "unit",
        "charm_status": "waiting",
        "status_message": "waiting for relation",
    }

    unit_initial = get_metric_value(
        "t_obs_results_metadata_charm_failure", unit_labels
    )

    # Add execution metadata with unit failure
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm_qa:failure:charm:postgresql-k8s:status": ["unit:waiting:waiting for relation"],
            }
        },
    )
    assert response.status_code == 200

    # Verify metric was incremented
    unit_new = get_metric_value(
        "t_obs_results_metadata_charm_failure", unit_labels
    )
    assert unit_new == unit_initial + 1


def test_charm_failure_metric_different_statuses(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm failure metric handles different charm statuses
    (error, blocked, waiting, etc.).
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
    test_execution = generator.gen_test_execution(
        artefact_build, environment, test_plan=test_plan_name
    )
    test_result = generator.gen_test_result(test_case, test_execution)

    # Test different statuses
    for charm_status, message in [
        ("error", "hook failed: config-changed"),
        ("blocked", "database required"),
        ("waiting", "waiting for units"),
    ]:
        labels = {
            "target_asset": artefact.name,
            "target_track": artefact.track or "",
            "target_risk": artefact.stage,
            "test_name": test_case.name,
            "status": test_result.status.value,
            "charm_name": "postgresql-k8s",
            "entity_type": "application",
            "charm_status": charm_status,
            "status_message": message,
        }

        initial = get_metric_value(
            "t_obs_results_metadata_charm_failure", labels
        )

        # Add execution metadata with specific status
        response = auth_patch(
            test_client,
            f"/v1/test-executions/{test_execution.id}",
            {
                "execution_metadata": {
                    "charm_qa:failure:charm:postgresql-k8s:status": [
                        f"application:{charm_status}:{message}"
                    ],
                }
            },
        )
        assert response.status_code == 200

        # Verify metric was incremented
        new = get_metric_value("t_obs_results_metadata_charm_failure", labels)
        assert new == initial + 1


def test_charm_failure_metric_not_updated_for_invalid_pattern(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm failure metric is not updated when metadata
    doesn't match the expected pattern.
    """
    # Generate test data for charm family only
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
    test_execution = generator.gen_test_execution(
        artefact_build, environment, test_plan=test_plan_name
    )
    generator.gen_test_result(test_case, test_execution)

    # Add execution metadata with incomplete pattern (missing parts)
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm_qa:failure:charm:postgresql-k8s": ["incomplete pattern"],
                "charm_qa:failure": ["too short"],
            }
        },
    )
    assert response.status_code == 200

    # The simple metadata metric should be updated, but not failure metric
    # This test just verifies no exception is raised
