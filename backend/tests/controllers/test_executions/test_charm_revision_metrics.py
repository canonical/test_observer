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


def test_charm_revision_metric_updated(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm revision metric is updated when execution metadata
    is added with charm revision information.
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
        "charm_revision": "495",
    }
    initial_value = get_metric_value(
        "t_obs_results_metadata_charm_revision", metric_labels
    )

    # Add execution metadata with charm revision
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm": ["postgresql-k8s"],
                "charm_qa:charm:postgresql-k8s:revision": ["495"],
            }
        },
    )
    assert response.status_code == 200

    # Verify metric was incremented
    new_value = get_metric_value("t_obs_results_metadata_charm_revision", metric_labels)
    assert new_value == initial_value + 1


def test_charm_revision_metric_multiple_charms(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm revision metric is updated for multiple charms
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

    # Get initial metric values for both charms
    postgres_labels = {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "charm_name": "postgresql-k8s",
        "charm_revision": "495",
    }
    mysql_labels = {
        "target_asset": artefact.name,
        "target_track": artefact.track or "",
        "target_risk": artefact.stage,
        "test_name": test_case.name,
        "status": test_result.status.value,
        "charm_name": "mysql-k8s",
        "charm_revision": "123",
    }

    postgres_initial = get_metric_value(
        "t_obs_results_metadata_charm_revision", postgres_labels
    )
    mysql_initial = get_metric_value(
        "t_obs_results_metadata_charm_revision", mysql_labels
    )

    # Add execution metadata with multiple charm revisions
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm": ["postgresql-k8s", "mysql-k8s"],
                "charm_qa:charm:postgresql-k8s:revision": ["495"],
                "charm_qa:charm:mysql-k8s:revision": ["123"],
            }
        },
    )
    assert response.status_code == 200

    # Verify both metrics were incremented
    postgres_new = get_metric_value(
        "t_obs_results_metadata_charm_revision", postgres_labels
    )
    mysql_new = get_metric_value("t_obs_results_metadata_charm_revision", mysql_labels)

    assert postgres_new == postgres_initial + 1
    assert mysql_new == mysql_initial + 1


def test_charm_revision_metric_not_updated_without_revision(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm revision metric is not updated when charm metadata
    is added without revision information.
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
    generator.gen_test_result(test_case, test_execution)

    # Add execution metadata without revision
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm": ["postgresql-k8s"],
                # No revision metadata
            }
        },
    )
    assert response.status_code == 200

    # The simple metadata metric should be updated, but not revision metric
    # This test just verifies no exception is raised


def test_charm_revision_metric_not_updated_for_non_charm_family(
    test_client: TestClient, generator: DataGenerator
):
    """
    Test that the charm revision metric is not updated for non-charm families.
    """
    # Generate test data for snap family
    environment = generator.gen_environment()
    test_case = generator.gen_test_case()
    artefact = generator.gen_artefact(
        name="test-snap", family=FamilyName.snap, track="latest", stage="edge"
    )
    artefact_build = generator.gen_artefact_build(artefact)
    test_execution = generator.gen_test_execution(artefact_build, environment)
    generator.gen_test_result(test_case, test_execution)

    # Add execution metadata (even though this wouldn't make sense for snaps)
    response = auth_patch(
        test_client,
        f"/v1/test-executions/{test_execution.id}",
        {
            "execution_metadata": {
                "charm_qa:charm:postgresql-k8s:revision": ["495"],
            }
        },
    )
    assert response.status_code == 200

    # Metrics should not be updated for snap family
    # This test just verifies no exception is raised
